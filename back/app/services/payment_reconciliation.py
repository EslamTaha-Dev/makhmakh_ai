from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.payment import Payment
from app.payments.types import PaymentStatus
from app.services.queue import payment_queue


settings = get_settings()

SCHEDULER_LOCK_KEY = (
    "makhmakh:payment-reconciliation:scheduler-lock"
)

SCHEDULER_LOCK_TTL = (
    settings.payment_reconciliation_interval_seconds + 60
)

RECONCILIATION_AGE = timedelta(hours=1)


def enqueue_pending_payment_jobs() -> None:
    db = SessionLocal()

    try:
        now = datetime.now(timezone.utc)
        fawry_cutoff = now - RECONCILIATION_AGE

        payments = db.scalars(
            select(Payment).where(
                Payment.status.in_(
                    [
                        PaymentStatus.PENDING.value,
                        PaymentStatus.PROCESSING.value,
                    ]
                )
            )
        ).all()

        for payment in payments:
            # Paymob: reconcile normally while payment is pending.
            # Fawry: only reconcile payments older than one hour.
            if payment.provider == "fawry":
                created_at = payment.created_at

                if created_at is None:
                    continue

                if created_at > fawry_cutoff:
                    continue

            payment_queue.enqueue(
                "app.services.payment_job.reconcile_payment_job",
                str(payment.id),
                job_timeout=300,
            )

    finally:
        db.close()


def reconcile_pending_payments_job() -> None:
    try:
        enqueue_pending_payment_jobs()

        payment_queue.enqueue(
            "app.services.subscription_job.expire_subscriptions_job",
            job_timeout=300,
        )

    finally:
        schedule_next_reconciliation()


def schedule_next_reconciliation() -> None:
    payment_queue.enqueue_in(
        settings.payment_reconciliation_interval_seconds,
        "app.services.payment_reconciliation.reconcile_pending_payments_job",
        job_timeout=300,
    )


def start_payment_reconciliation() -> None:
    try:
        acquired = payment_queue.connection.set(
            SCHEDULER_LOCK_KEY,
            "1",
            nx=True,
            ex=SCHEDULER_LOCK_TTL,
        )

        if not acquired:
            return

        payment_queue.enqueue(
            "app.services.payment_reconciliation.reconcile_pending_payments_job",
            job_timeout=300,
        )

    except Exception:
        return