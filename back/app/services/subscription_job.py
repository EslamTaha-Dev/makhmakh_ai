from datetime import datetime, timezone

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.subscription import Subscription


def expire_subscriptions_job() -> None:
    db = SessionLocal()

    try:
        now = datetime.now(timezone.utc)

        subscriptions = db.scalars(
            select(Subscription).where(
                Subscription.status == "active",
                Subscription.ends_at.is_not(None),
                Subscription.ends_at <= now,
            )
        ).all()

        for subscription in subscriptions:
            subscription.status = "expired"

        if subscriptions:
            db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()