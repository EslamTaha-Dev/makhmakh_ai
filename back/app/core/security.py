from datetime import datetime, timedelta, timezone
import hashlib
import secrets

import jwt
from cryptography.fernet import Fernet, InvalidToken
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from passlib.context import CryptContext

from app.core.config import get_settings


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

argon2_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    return argon2_hasher.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    if hashed_password.startswith("$argon2"):
        try:
            return argon2_hasher.verify(hashed_password, plain_password)
        except (VerifyMismatchError, InvalidHashError):
            return False

    return pwd_context.verify(plain_password, hashed_password)


def password_needs_rehash(hashed_password: str) -> bool:
    return hashed_password.startswith("$argon2") and argon2_hasher.check_needs_rehash(hashed_password)


def create_access_token(user_id: str) -> str:
    settings = get_settings()

    expire = datetime.now(timezone.utc) + timedelta(seconds=settings.jwt_access_token_ttl_seconds)

    payload = {
        "sub": user_id,
        "type": "access",
        "exp": expire,
    }

    signing_key = settings.jwt_private_key or settings.jwt_secret_key

    return jwt.encode(
        payload,
        signing_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(user_id: str) -> str:
    settings = get_settings()

    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )

    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": expire,
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
def decode_token(token: str) -> dict:
    settings = get_settings()

    verification_key = settings.jwt_public_key or settings.jwt_secret_key

    return jwt.decode(
        token,
        verification_key,
        algorithms=[settings.jwt_algorithm],
    )


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def generate_one_time_token() -> str:
    return secrets.token_urlsafe(48)


def encrypt_mfa_secret(secret: str) -> str:
    key = get_settings().mfa_encryption_key
    if not key:
        if get_settings().environment == "development":
            return secret
        raise RuntimeError("MFA_ENCRYPTION_KEY is required")
    return Fernet(key.encode()).encrypt(secret.encode()).decode()


def decrypt_mfa_secret(secret: str) -> str:
    key = get_settings().mfa_encryption_key
    if not key or not secret.startswith("gAAAA"):
        return secret
    try:
        return Fernet(key.encode()).decrypt(secret.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Stored MFA secret cannot be decrypted") from exc