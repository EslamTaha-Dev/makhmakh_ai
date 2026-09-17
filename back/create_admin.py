from getpass import getpass

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import hash_password


def main():
    print("=== Create makhmakh Admin ===")

    name = input("Admin name: ").strip()
    email = input("Admin email: ").strip().lower()
    password = getpass("Admin password: ")
    confirm_password = getpass("Confirm password: ")

    if not name or not email or not password:
        print("Error: all fields are required.")
        return

    if password != confirm_password:
        print("Error: passwords do not match.")
        return

    if len(password) < 8:
        print("Error: password must be at least 8 characters.")
        return

    db = SessionLocal()

    try:
        existing_user = db.scalar(
            select(User).where(User.email == email)
        )

        if existing_user:
            print(f"Error: user with email {email} already exists.")
            return

        admin = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role="admin",
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("\nAdmin created successfully!")
        print(f"Name: {admin.name}")
        print(f"Email: {admin.email}")
        print(f"Role: {admin.role}")
        print(f"ID: {admin.id}")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    main()