from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.user import User
from app.models.role import Role, UserRole

db = SessionLocal()

try:
    user = db.scalar(
        select(User).order_by(User.created_at.desc())
    )

    if user is None:
        print("No users found.")
    else:
        role = db.scalar(
            select(Role).where(Role.name == "admin")
        )

        user.role = "admin"

        existing = db.scalar(
            select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.role_id == role.id,
            )
        )

        if existing is None:
            db.add(
                UserRole(
                    user_id=user.id,
                    role_id=role.id,
                )
            )

        db.commit()

        print("ADMIN CREATED SUCCESSFULLY")
        print("Email:", user.email)
        print("Role:", user.role)

finally:
    db.close()
