from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.db.session import get_db
from app.models.role import Role, UserRole
from app.models.user import User


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


ADMIN_ROLES = ("admin", "super_admin")

ALLOWED_ROLES = {
    "student",
    "instructor",
    "content_creator",
    "support",
    "admin",
    "super_admin",
}


class UpdateUserRoleRequest(BaseModel):
    role: str = Field(
        min_length=1,
        max_length=50,
    )


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*ADMIN_ROLES)
    ),
):
    users = db.scalars(
        select(User).order_by(User.created_at.desc())
    ).all()

    return [
        {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "created_at": user.created_at,
        }
        for user in users
    ]


@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: UUID,
    data: UpdateUserRoleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*ADMIN_ROLES)
    ),
):
    new_role = data.role.strip().lower()

    if new_role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=400,
            detail="Invalid role",
        )

    user = db.scalar(
        select(User).where(User.id == user_id)
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # Only super_admin can manage another super_admin.
    if (
        user.role == "super_admin"
        and current_user.role != "super_admin"
    ):
        raise HTTPException(
            status_code=403,
            detail="Only super_admin can modify a super_admin",
        )

    # Only super_admin can grant super_admin.
    if (
        new_role == "super_admin"
        and current_user.role != "super_admin"
    ):
        raise HTTPException(
            status_code=403,
            detail="Only super_admin can assign super_admin role",
        )

    # Prevent an admin from accidentally removing their own admin access.
    if user.id == current_user.id and new_role not in ADMIN_ROLES:
        raise HTTPException(
            status_code=400,
            detail="You cannot remove your own admin privileges",
        )

    role = db.scalar(
        select(Role).where(Role.name == new_role)
    )

    if role is None:
        raise HTTPException(
            status_code=404,
            detail="Role not found",
        )

    # Keep the legacy role column synchronized.
    user.role = new_role

    # Remove previous RBAC assignments.
    db.execute(
        delete(UserRole).where(
            UserRole.user_id == user.id
        )
    )

    # Add exactly one current RBAC role.
    db.add(
        UserRole(
            user_id=user.id,
            role_id=role.id,
        )
    )

    db.commit()
    db.refresh(user)

    return {
        "message": "User role updated successfully",
        "user_id": str(user.id),
        "role": user.role,
    }