from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.payment import Payment
from app.payments.service import (
    apply_payment_status,
    get_payment_provider,
)
from app.payments.types import PaymentStatus


def reconcile_payment_job(
    payment_id: str,
) -> None:
    db = SessionLocal()

    try:
        payment = db.scalar(
            select(Payment).where(
                Payment.id == payment_id
            )
        )

        if payment is None:
            raise ValueError(
                f"Payment not found: {payment_id}"
            )

        if payment.status not in {
            PaymentStatus.PENDING.value,
            PaymentStatus.PROCESSING.value,
        }:
            return

        if not payment.external_id:
            return

        provider = get_payment_provider(
            payment.provider
        )

        provider_status = provider.get_payment_status(
            payment.external_id
        )

        normalized_status = (
            str(provider_status)
            .strip()
            .lower()
        )

        if normalized_status in {
            "paid",
            "success",
            "successful",
            "completed",
            "captured",
        }:
            new_status = PaymentStatus.PAID

        elif normalized_status in {
            "failed",
            "failure",
            "rejected",
            "declined",
        }:
            new_status = PaymentStatus.FAILED

        elif normalized_status in {
            "cancelled",
            "canceled",
            "voided",
        }:
            new_status = PaymentStatus.CANCELED

        elif normalized_status in {
            "processing",
            "pending",
            "initiated",
            "in_progress",
        }:
            new_status = PaymentStatus.PROCESSING

        else:
            return

        apply_payment_status(
            db=db,
            payment=payment,
            new_status=new_status,
            commit=True,
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()