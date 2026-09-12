from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.rate_limit import limiter
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.db.session import get_db
from app.models.refresh_token import RefreshToken
from app.models.role import Role, UserRole
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.security_events import record_security_event


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


MAX_FAILED_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


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

    record_security_event(
        db=db,
        event_type="user_registered",
        user_id=user.id,
    )

    db.commit()
    db.refresh(user)

    return user


@limiter.limit("5/minute")
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

    if stored_token.revoked:
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

    now = datetime.now(timezone.utc)

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
            revoked=True
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