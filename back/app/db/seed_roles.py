from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.role import Role, UserRole
from app.models.user import User


ROLES = [
    ("student", "Student user"),
    ("instructor", "Instructor"),
    ("content_creator", "Content creator"),
    ("support", "Support staff"),
    ("admin", "Administrator"),
    ("super_admin", "Super administrator"),
]


def seed_roles():
    db = SessionLocal()

    try:
        for role_name, description in ROLES:
            existing_role = db.scalar(
                select(Role).where(Role.name == role_name)
            )

            if existing_role is None:
                db.add(
                    Role(
                        name=role_name,
                        description=description,
                    )
                )

        db.commit()
        roles = {
            role.name: role
            for role in db.scalars(select(Role)).all()
        }
        users = db.scalars(select(User)).all()

        for user in users:
            role_name = user.role or "student"

            role = roles.get(role_name)

            if role is None:
                role = roles["student"]

            existing_user_role = db.scalar(
                select(UserRole).where(
                    UserRole.user_id == user.id,
                    UserRole.role_id == role.id,
                )
            )

            if existing_user_role is None:
                db.add(
                    UserRole(
                        user_id=user.id,
                        role_id=role.id,
                    )
                )

        db.commit()

        print("Roles seeded successfully.")
        print("Existing users assigned to roles successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_roles()