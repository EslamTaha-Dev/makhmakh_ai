from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials

    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )

    user = db.scalar(
        select(User).where(User.id == user_id)
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


def get_user_roles(
    user: User,
) -> set[str]:
    roles = {
        user_role.role.name
        for user_role in user.user_roles
        if user_role.role is not None
    }

    # Temporary backward compatibility with the existing role column.
    if not roles and user.role:
        roles.add(user.role)

    return roles


def require_roles(*allowed_roles: str):
    allowed = set(allowed_roles)

    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        user_roles = get_user_roles(current_user)

        if not user_roles.intersection(allowed):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return role_checker


def require_admin(
    current_user: User = Depends(
        require_roles("admin", "super_admin")
    ),
) -> User:
    return current_user


def require_student(
    current_user: User = Depends(
        require_roles("student")
    ),
) -> User:
    return current_user


def require_instructor(
    current_user: User = Depends(
        require_roles("instructor")
    ),
) -> User:
    return current_user


def require_content_creator(
    current_user: User = Depends(
        require_roles("content_creator")
    ),
) -> User:
    return current_user


def require_support(
    current_user: User = Depends(
        require_roles("support")
    ),
) -> User:
    return current_user


def require_super_admin(
    current_user: User = Depends(
        require_roles("super_admin")
    ),
) -> User:
    return current_user