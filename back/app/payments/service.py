import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.course import Course
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.user import User
from app.payments.fawry import FawryProvider
from app.payments.paymob import PaymobProvider
from app.payments.provider import PaymentProvider
from app.payments.types import (
    CustomerInfo,
    PaymentRequest,
    PaymentStatus,
)
from app.services.queue import payment_queue


def get_payment_provider(
    provider_name: str,
) -> PaymentProvider:
    provider_name = provider_name.lower().strip()

    if provider_name == "paymob":
        return PaymobProvider()

    if provider_name == "fawry":
        return FawryProvider()

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported payment provider",
    )


def create_invoice(
    db: Session,
    payment: Payment,
) -> Invoice:
    existing_invoice = db.scalar(
        select(Invoice).where(
            Invoice.payment_id == payment.id
        )
    )

    if existing_invoice is not None:
        return existing_invoice

    invoice = Invoice(
        payment_id=payment.id,
        amount=payment.amount,
        currency=payment.currency,
        status="paid",
        issued_at=datetime.now(timezone.utc),
        paid_at=payment.paid_at,
    )

    db.add(invoice)
    db.flush()

    return invoice


def enqueue_payment_reconciliation(
    payment_id: str,
) -> None:
    payment_queue.enqueue(
        "app.services.payment_job.reconcile_payment_job",
        payment_id,
        job_timeout=300,
    )


def _get_existing_payment(
    db: Session,
    idempotency_key: str,
) -> Payment | None:
    return db.scalar(
        select(Payment).where(
            Payment.idempotency_key == idempotency_key
        )
    )


def _validate_idempotent_request(
    payment: Payment,
    *,
    user: User,
    course: Course,
    amount: Decimal,
    currency: str,
    provider_name: str,
) -> Payment:
    if payment.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency-Key is already associated with another user",
        )

    if payment.course_id != course.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency-Key was already used for another course",
        )

    if payment.amount != amount:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency-Key was already used with another amount",
        )

    if payment.currency != currency:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency-Key was already used with another currency",
        )

    if payment.provider != provider_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency-Key was already used with another payment provider",
        )

    return payment


def _get_active_or_pending_subscription(
    db: Session,
    *,
    user_id: uuid.UUID,
    course_id: uuid.UUID,
) -> Subscription | None:
    return db.scalar(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.course_id == course_id,
            Subscription.status.in_(
                ["pending", "active"]
            ),
        )
    )


def _get_subscription_payment(
    db: Session,
    subscription_id: uuid.UUID,
) -> Payment | None:
    return db.scalar(
        select(Payment)
        .where(
            Payment.subscription_id == subscription_id,
            Payment.status.in_(
                [
                    PaymentStatus.PENDING.value,
                    PaymentStatus.PROCESSING.value,
                    PaymentStatus.PAID.value,
                ]
            ),
        )
        .order_by(
            Payment.created_at.desc()
        )
    )


def create_payment(
    db: Session,
    *,
    user: User,
    course: Course,
    amount: Decimal,
    currency: str,
    provider_name: str,
    idempotency_key: str,
    callback_url: str | None = None,
) -> Payment:
    idempotency_key = idempotency_key.strip()
    provider_name = provider_name.lower().strip()
    currency = currency.upper().strip()

    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key cannot be empty",
        )

    if len(idempotency_key) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key is too long",
        )

    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount must be greater than zero",
        )

    # True idempotency replay.
    existing_payment = _get_existing_payment(
        db,
        idempotency_key,
    )

    if existing_payment is not None:
        return _validate_idempotent_request(
            existing_payment,
            user=user,
            course=course,
            amount=amount,
            currency=currency,
            provider_name=provider_name,
        )

    # Prevent creating another payment for an already
    # pending/active subscription.
    existing_subscription = _get_active_or_pending_subscription(
        db,
        user_id=user.id,
        course_id=course.id,
    )

    if existing_subscription is not None:
        existing_payment = _get_subscription_payment(
            db,
            existing_subscription.id,
        )

        if existing_payment is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "You already have a pending or active payment "
                    "for this course. Reuse the original Idempotency-Key."
                ),
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "You already have an active or pending "
                "subscription for this course"
            ),
        )

    subscription = Subscription(
        user_id=user.id,
        course_id=course.id,
        provider=provider_name,
        status="pending",
    )

    db.add(subscription)

    try:
        db.flush()

        payment = Payment(
            user_id=user.id,
            course_id=course.id,
            subscription_id=subscription.id,
            provider=provider_name,
            status=PaymentStatus.PENDING.value,
            amount=amount,
            currency=currency,
            idempotency_key=idempotency_key,
        )

        db.add(payment)

        db.flush()

    except IntegrityError:
        db.rollback()

        # Another request may have won the race.
        existing_payment = _get_existing_payment(
            db,
            idempotency_key,
        )

        if existing_payment is not None:
            return _validate_idempotent_request(
                existing_payment,
                user=user,
                course=course,
                amount=amount,
                currency=currency,
                provider_name=provider_name,
            )

        existing_subscription = _get_active_or_pending_subscription(
            db,
            user_id=user.id,
            course_id=course.id,
        )

        if existing_subscription is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "A payment or subscription is already "
                    "being created for this course"
                ),
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A payment or subscription is already "
                "being created for this course"
            ),
        )

    customer = CustomerInfo(
        name=user.name,
        email=user.email,
    )

    request = PaymentRequest(
        amount=amount,
        currency=currency,
        order_id=str(payment.id),
        customer=customer,
        callback_url=callback_url,
        metadata={
            "payment_id": str(payment.id),
            "subscription_id": str(subscription.id),
            "course_id": str(course.id),
            "user_id": str(user.id),
        },
    )

    provider = get_payment_provider(provider_name)

    try:
        checkout = provider.create_checkout(request)

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payment provider is currently unavailable",
        ) from exc

    payment.external_id = checkout.external_id
    payment.checkout_url = checkout.checkout_url
    payment.status = checkout.status.value

    try:
        db.commit()

    except IntegrityError:
        db.rollback()

        existing_payment = _get_existing_payment(
            db,
            idempotency_key,
        )

        if existing_payment is not None:
            return _validate_idempotent_request(
                existing_payment,
                user=user,
                course=course,
                amount=amount,
                currency=currency,
                provider_name=provider_name,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment request could not be completed safely",
        )

    db.refresh(payment)

    if payment.status in {
        PaymentStatus.PENDING.value,
        PaymentStatus.PROCESSING.value,
    }:
        try:
            enqueue_payment_reconciliation(
                str(payment.id)
            )
        except Exception:
            pass

    return payment


def apply_payment_status(
    db: Session,
    payment: Payment,
    new_status: PaymentStatus,
    *,
    commit: bool = True,
) -> Payment:
    try:
        current_status = PaymentStatus(payment.status)

    except ValueError:
        return payment

    allowed_transitions = {
        PaymentStatus.PENDING: {
            PaymentStatus.PROCESSING,
            PaymentStatus.PAID,
            PaymentStatus.FAILED,
            PaymentStatus.CANCELED,
        },
        PaymentStatus.PROCESSING: {
            PaymentStatus.PAID,
            PaymentStatus.FAILED,
            PaymentStatus.CANCELED,
        },
        PaymentStatus.PAID: {
            PaymentStatus.REFUNDED,
        },
        PaymentStatus.FAILED: set(),
        PaymentStatus.CANCELED: set(),
        PaymentStatus.REFUNDED: set(),
    }

    if new_status == current_status:
        return payment

    if new_status not in allowed_transitions.get(
        current_status,
        set(),
    ):
        return payment

    payment.status = new_status.value

    if new_status == PaymentStatus.PAID:
        now = datetime.now(timezone.utc)

        payment.paid_at = now

        if payment.subscription is not None:
            settings = get_settings()

            payment.subscription.status = "active"
            payment.subscription.starts_at = now
            payment.subscription.ends_at = (
                now
                + timedelta(
                    days=settings.subscription_duration_days
                )
            )
            payment.subscription.canceled_at = None

        create_invoice(
            db=db,
            payment=payment,
        )

    elif new_status in {
        PaymentStatus.FAILED,
        PaymentStatus.CANCELED,
    }:
        if payment.subscription is not None:
            payment.subscription.status = "canceled"
            payment.subscription.canceled_at = datetime.now(
                timezone.utc
            )

    elif new_status == PaymentStatus.REFUNDED:
        if payment.subscription is not None:
            payment.subscription.status = "canceled"
            payment.subscription.canceled_at = datetime.now(
                timezone.utc
            )

    if commit:
        db.commit()
        db.refresh(payment)
    else:
        db.flush()

    return payment