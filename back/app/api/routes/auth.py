import uuid
import pyotp
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.rate_limit import limiter
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    generate_one_time_token,
    encrypt_mfa_secret,
    decrypt_mfa_secret,
    password_needs_rehash,
    verify_password,
)
from app.db.session import get_db
from app.models.refresh_token import RefreshToken
from app.models.role import Role, UserRole
from app.models.user import User
from app.models.temporary_token import PasswordResetToken, EmailVerificationToken
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    ChangePasswordRequest,
)
from app.services.security_events import record_security_event
from app.services.queue import email_queue


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


MAX_FAILED_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):
    existing_user = db.scalar(
        select(User).where(
            User.email == data.email.lower()
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    student_role = db.scalar(
        select(Role).where(
            Role.name == "student"
        )
    )

    if student_role is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default student role is not configured",
        )

    user = User(
        name=data.name.strip(),
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        role="student",
        failed_login_attempts=0,
    )

    db.add(user)
    db.flush()

    user_role = UserRole(
        user_id=user.id,
        role_id=student_role.id,
    )

    db.add(user_role)

    verification_token = generate_one_time_token()
    db.add(
        EmailVerificationToken(
            user_id=user.id,
            token_hash=hash_refresh_token(verification_token),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
    )

    record_security_event(
        db=db,
        event_type="user_registered",
        user_id=user.id,
    )

    db.commit()
    db.refresh(user)

    try:
        email_queue.enqueue(
            "app.services.email_job.send_email_job",
            user.email,
            "Verify your Bosla email",
            f"Verify your email: {get_settings().email_verification_url}?token={verification_token}",
            job_timeout=60,
        )
    except Exception:
        pass

    response = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "created_at": user.created_at,
    }
    if get_settings().environment == "development":
        response["verification_token"] = verification_token
    return response


@router.post("/verify-email")
def verify_email(data: VerifyEmailRequest, db: Session = Depends(get_db)):
    token = db.scalar(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == hash_refresh_token(data.token),
            EmailVerificationToken.used_at.is_(None),
        )
    )
    now = datetime.now(timezone.utc)
    if token is None or token.expires_at <= now:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")
    user = db.scalar(select(User).where(User.id == token.user_id))
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid verification token")
    token.used_at = now
    user.email_verified_at = now
    db.commit()
    return {"status": "verified"}


@limiter.limit("3/hour")
@router.post("/forgot-password")
def forgot_password(request: Request, data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if user is not None:
        raw_token = generate_one_time_token()
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hash_refresh_token(raw_token),
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
            )
        )
        record_security_event(db=db, event_type="password_reset_requested", user_id=user.id, request=request)
        db.commit()
        try:
            email_queue.enqueue(
                "app.services.email_job.send_email_job",
                user.email,
                "Reset your Bosla password",
                f"Reset your password: {get_settings().password_reset_url}?token={raw_token}",
                job_timeout=60,
            )
        except Exception:
            pass
        response = {"status": "accepted"}
        if get_settings().environment == "development":
            response["reset_token"] = raw_token
        return response
    return {"status": "accepted"}


@router.post("/reset-password")
def reset_password(request: Request, data: ResetPasswordRequest, db: Session = Depends(get_db)):
    token = db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == hash_refresh_token(data.token),
            PasswordResetToken.used_at.is_(None),
        )
    )
    now = datetime.now(timezone.utc)
    if token is None or token.expires_at <= now:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    user = db.scalar(select(User).where(User.id == token.user_id))
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid reset token")
    user.password_hash = hash_password(data.new_password)
    token.used_at = now
    db.execute(update(RefreshToken).where(RefreshToken.user_id == user.id).values(revoked=True, revoked_at=now, revoked_reason="password_changed"))
    record_security_event(db=db, event_type="password_reset_completed", user_id=user.id, request=request)
    db.commit()
    return {"status": "password_reset"}


@router.post("/change-password")
def change_password(request: Request, data: ChangePasswordRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Current password is invalid")
    current_user.password_hash = hash_password(data.new_password)
    now = datetime.now(timezone.utc)
    db.execute(update(RefreshToken).where(RefreshToken.user_id == current_user.id).values(revoked=True, revoked_at=now, revoked_reason="password_changed"))
    record_security_event(db=db, event_type="password_changed", user_id=current_user.id, request=request)
    db.commit()
    return {"status": "password_changed"}


@limiter.limit("5/15minutes")
@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    request: Request,
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(
            User.email == data.email.lower()
        )
    )

    if user is None:
        record_security_event(
            db=db,
            event_type="login_failed",
            request=request,
            details={"reason": "invalid_credentials"},
        )

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active",
        )

    now = datetime.now(timezone.utc)

    if user.locked_until is not None:
        locked_until = user.locked_until

        if locked_until > now:
            record_security_event(
                db=db,
                event_type="login_blocked",
                user_id=user.id,
                request=request,
                details={
                    "reason": "account_locked"
                },
            )

            db.commit()

            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account temporarily locked. Please try again later.",
            )

        user.locked_until = None
        user.failed_login_attempts = 0

        db.commit()

    if not verify_password(
        data.password,
        user.password_hash,
    ):
        user.failed_login_attempts += 1

        record_security_event(
            db=db,
            event_type="login_failed",
            user_id=user.id,
            request=request,
            details={
                "reason": "invalid_password",
                "failed_attempts": user.failed_login_attempts,
            },
        )

        if (
            user.failed_login_attempts
            >= MAX_FAILED_LOGIN_ATTEMPTS
        ):
            user.locked_until = (
                now
                + timedelta(
                    minutes=LOCKOUT_MINUTES
                )
            )

            record_security_event(
                db=db,
                event_type="account_locked",
                user_id=user.id,
                request=request,
                details={
                    "reason": "too_many_failed_login_attempts",
                    "failed_attempts": user.failed_login_attempts,
                    "lockout_minutes": LOCKOUT_MINUTES,
                },
            )

            db.commit()

            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account temporarily locked due to too many failed login attempts.",
            )

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = now

    if not user.password_hash.startswith("$argon2"):
        user.password_hash = hash_password(data.password)
    elif password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(data.password)

    access_token = create_access_token(
        str(user.id)
    )

    refresh_token = generate_refresh_token()

    refresh_token_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(
            refresh_token
        ),
        expires_at=(
            now
            + timedelta(
                days=REFRESH_TOKEN_EXPIRE_DAYS
            )
        ),
        revoked=False,
        family_id=uuid.uuid4(),
        device_label=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )

    db.add(refresh_token_record)

    record_security_event(
        db=db,
        event_type="login_success",
        user_id=user.id,
        request=request,
    )

    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh_token(
    request: Request,
    data: RefreshRequest,
    db: Session = Depends(get_db),
):
    token_hash = hash_refresh_token(
        data.refresh_token
    )

    stored_token = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash
        )
    )

    if stored_token is None:
        record_security_event(
            db=db,
            event_type="refresh_token_invalid",
            request=request,
        )

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    now = datetime.now(timezone.utc)

    if stored_token.revoked:
        db.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == stored_token.family_id)
            .values(
                revoked=True,
                revoked_at=now,
                revoked_reason="reuse_detected",
            )
        )
        record_security_event(
            db=db,
            event_type="refresh_token_reuse",
            user_id=stored_token.user_id,
            request=request,
            details={
                "reason": "revoked_refresh_token_reused"
            },
        )

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    if stored_token.expires_at <= now:
        stored_token.revoked = True

        record_security_event(
            db=db,
            event_type="refresh_token_expired",
            user_id=stored_token.user_id,
            request=request,
        )

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )

    user = db.scalar(
        select(User).where(
            User.id == stored_token.user_id
        )
    )

    if user is None:
        stored_token.revoked = True

        record_security_event(
            db=db,
            event_type="refresh_token_user_not_found",
            request=request,
        )

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    stored_token.revoked = True
    stored_token.revoked_at = now
    stored_token.revoked_reason = "rotation"

    new_access_token = create_access_token(
        str(user.id)
    )

    new_refresh_token = generate_refresh_token()

    new_refresh_token_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(
            new_refresh_token
        ),
        expires_at=(
            now
            + timedelta(
                days=REFRESH_TOKEN_EXPIRE_DAYS
            )
        ),
        revoked=False,
        family_id=stored_token.family_id,
        device_label=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )

    db.add(new_refresh_token_record)

    record_security_event(
        db=db,
        event_type="refresh_token_rotated",
        user_id=user.id,
        request=request,
    )

    db.commit()

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
    )


@router.get("/sessions")
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sessions = db.scalars(
        select(RefreshToken)
        .where(
            RefreshToken.user_id == current_user.id,
            RefreshToken.revoked.is_(False),
        )
        .order_by(RefreshToken.created_at.desc())
    ).all()
    return [
        {
            "id": str(session.id),
            "family_id": str(session.family_id),
            "device_label": session.device_label,
            "ip_address": session.ip_address,
            "created_at": session.created_at,
            "expires_at": session.expires_at,
        }
        for session in sessions
    ]


@router.delete("/sessions/{session_id}")
def revoke_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.scalar(
        select(RefreshToken).where(
            RefreshToken.id == session_id,
            RefreshToken.user_id == current_user.id,
        )
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    session.revoked = True
    session.revoked_at = datetime.now(timezone.utc)
    session.revoked_reason = "logout"
    db.commit()
    return {"status": "revoked"}


@router.delete("/sessions")
def revoke_all_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == current_user.id, RefreshToken.revoked.is_(False))
        .values(revoked=True, revoked_at=now, revoked_reason="logout_all")
    )
    db.commit()
    return {"status": "revoked_all"}


@router.post("/mfa/setup")
def setup_mfa(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.mfa import MFASecret

    secret = pyotp.random_base32()
    record = db.scalar(select(MFASecret).where(MFASecret.user_id == current_user.id))
    if record is None:
        record = MFASecret(user_id=current_user.id, totp_secret=encrypt_mfa_secret(secret))
        db.add(record)
    else:
        record.totp_secret = encrypt_mfa_secret(secret)
        record.enabled_at = None
    db.commit()
    return {
        "secret": secret,
        "provisioning_uri": pyotp.TOTP(secret).provisioning_uri(
            name=current_user.email,
            issuer_name="Bosla",
        ),
    }


@router.post("/mfa/verify")
def verify_mfa(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.mfa import MFASecret

    record = db.scalar(select(MFASecret).where(MFASecret.user_id == current_user.id))
    if record is None or not pyotp.TOTP(decrypt_mfa_secret(record.totp_secret)).verify(code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid MFA code")
    record.enabled_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "enabled"}


@router.post("/mfa/recovery-codes")
def create_mfa_recovery_codes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.mfa import MFASecret, MFARecoveryCode

    secret = db.scalar(select(MFASecret).where(MFASecret.user_id == current_user.id))
    if secret is None or secret.enabled_at is None:
        raise HTTPException(status_code=409, detail="MFA is not enabled")
    db.query(MFARecoveryCode).filter(MFARecoveryCode.user_id == current_user.id, MFARecoveryCode.used_at.is_(None)).delete(synchronize_session=False)
    codes = [secrets.token_urlsafe(8) for _ in range(8)]
    for code in codes:
        db.add(MFARecoveryCode(user_id=current_user.id, code_hash=hash_refresh_token(code)))
    db.commit()
    return {"recovery_codes": codes}


@router.post("/mfa/recovery-codes/verify")
def verify_mfa_recovery_code(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.mfa import MFARecoveryCode

    recovery = db.scalar(select(MFARecoveryCode).where(MFARecoveryCode.user_id == current_user.id, MFARecoveryCode.code_hash == hash_refresh_token(code), MFARecoveryCode.used_at.is_(None)))
    if recovery is None:
        raise HTTPException(status_code=400, detail="Invalid recovery code")
    recovery.used_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "accepted"}


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.post("/logout")
def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.user_id == current_user.id,
            RefreshToken.revoked.is_(False),
        )
        .values(
            revoked=True,
            revoked_at=datetime.now(timezone.utc),
            revoked_reason="logout",
        )
    )

    record_security_event(
        db=db,
        event_type="logout",
        user_id=current_user.id,
        request=request,
    )

    db.commit()

    return {
        "message": "Logged out successfully"
    }