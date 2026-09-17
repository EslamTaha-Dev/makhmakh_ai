import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.payment import Payment
from app.payments.service import apply_payment_status, get_payment_provider
from app.payments.types import PaymentStatus


async def reconcile_pending_fawry_payments(ctx: dict) -> int:
    del ctx
    settings = get_settings()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    db = SessionLocal()
    updated = 0

    try:
        payments = db.scalars(
            select(Payment).where(
                Payment.provider == "fawry",
                Payment.status.in_(
                    [
                        PaymentStatus.PENDING.value,
                        PaymentStatus.PROCESSING.value,
                        PaymentStatus.PENDING_RECONCILIATION.value,
                    ]
                ),
                Payment.created_at <= cutoff,
                Payment.external_id.is_not(None),
            )
        ).all()

        for payment in payments:
            provider = get_payment_provider(payment.provider)
            provider_status = await asyncio.to_thread(
                provider.get_payment_status,
                payment.external_id,
            )
            normalized = str(provider_status).strip().lower()

            status_map = {
                "paid": PaymentStatus.PAID,
                "success": PaymentStatus.PAID,
                "successful": PaymentStatus.PAID,
                "completed": PaymentStatus.PAID,
                "failed": PaymentStatus.FAILED,
                "failure": PaymentStatus.FAILED,
                "rejected": PaymentStatus.FAILED,
                "expired": PaymentStatus.EXPIRED,
                "cancelled": PaymentStatus.CANCELED,
                "canceled": PaymentStatus.CANCELED,
                "pending": PaymentStatus.PENDING,
                "processing": PaymentStatus.PROCESSING,
            }
            new_status = status_map.get(normalized)

            if new_status is None:
                continue

            old_status = payment.status
            apply_payment_status(
                db,
                payment,
                new_status,
                commit=False,
            )

            if payment.status != old_status:
                updated += 1

        if updated:
            db.commit()

        return updated
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
