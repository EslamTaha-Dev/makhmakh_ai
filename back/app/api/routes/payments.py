import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Request,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_student
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.course import Course
from app.models.payment import Payment
from app.models.payment_event import PaymentEvent
from app.models.user import User
from app.payments.service import (
    apply_payment_status,
    create_payment,
    get_payment_provider,
)


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


PAYMENT_CURRENCY = "EGP"


class CreatePaymentRequest(BaseModel):
    course_id: uuid.UUID

    provider: str = Field(
        default="paymob",
        min_length=3,
        max_length=30,
    )

    callback_url: str | None = None


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/hour")
def create_payment_endpoint(
    request: Request,
    data: CreatePaymentRequest,
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    course = db.scalar(
        select(Course).where(
            Course.id == data.course_id
        )
    )

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    amount = Decimal(course.price)

    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This course is not available for paid subscription",
        )

    provider_name = data.provider.lower().strip()

    payment = create_payment(
        db=db,
        user=current_user,
        course=course,
        amount=amount,
        currency=PAYMENT_CURRENCY,
        provider_name=provider_name,
        idempotency_key=idempotency_key,
        callback_url=data.callback_url,
    )

    return {
        "id": str(payment.id),
        "course_id": str(payment.course_id),
        "amount": str(payment.amount),
        "currency": payment.currency,
        "provider": payment.provider,
        "status": payment.status,
        "checkout_url": payment.checkout_url,
        "external_id": payment.external_id,
        "created_at": payment.created_at,
    }


@router.get(
    "/{payment_id}",
)
def get_payment(
    payment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = db.scalar(
        select(Payment).where(
            Payment.id == payment_id,
            Payment.user_id == current_user.id,
        )
    )

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    return {
        "id": str(payment.id),
        "course_id": str(payment.course_id),
        "amount": str(payment.amount),
        "currency": payment.currency,
        "provider": payment.provider,
        "status": payment.status,
        "checkout_url": payment.checkout_url,
        "external_id": payment.external_id,
        "failure_reason": payment.failure_reason,
        "paid_at": payment.paid_at,
        "created_at": payment.created_at,
        "updated_at": payment.updated_at,
    }


def get_payment_from_webhook(
    db: Session,
    *,
    provider_name: str,
    external_id: str | None,
    payload: dict,
) -> Payment | None:
    if external_id:
        payment = db.scalar(
            select(Payment).where(
                Payment.provider == provider_name,
                Payment.external_id == external_id,
            )
        )

        if payment is not None:
            return payment

    payment_id = payload.get("payment_id")

    if payment_id:
        try:
            payment_uuid = uuid.UUID(
                str(payment_id)
            )
        except (ValueError, TypeError):
            payment_uuid = None

        if payment_uuid is not None:
            return db.scalar(
                select(Payment).where(
                    Payment.id == payment_uuid,
                    Payment.provider == provider_name,
                )
            )

    return None


def process_webhook(
    *,
    provider_name: str,
    payload: dict,
    signature: str | None,
    db: Session,
):
    provider_name = provider_name.lower().strip()

    provider = get_payment_provider(provider_name)

    try:
        result = provider.verify_webhook(
            payload=payload,
            signature=signature,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    if not result.event_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook event ID is required",
        )

    # Webhook events are unique per provider.
    # Paymob and Fawry may legally use the same event_id.
    existing_event = db.scalar(
        select(PaymentEvent).where(
            PaymentEvent.provider == provider_name,
            PaymentEvent.event_id == result.event_id,
        )
    )

    if existing_event is not None:
        return {
            "status": "already_processed",
            "event_id": result.event_id,
            "provider": provider_name,
        }

    payment = get_payment_from_webhook(
        db=db,
        provider_name=provider_name,
        external_id=result.external_id,
        payload=payload,
    )

    event = PaymentEvent(
        payment_id=payment.id if payment else None,
        provider=provider_name,
        event_id=result.event_id,
        event_type=result.event_type,
        payload=result.payload,
        signature=result.signature,
        processed=False,
    )

    db.add(event)

    try:
        db.flush()

    except IntegrityError:
        db.rollback()

        # Another request may have inserted the same provider/event_id
        # at the same time.
        existing_event = db.scalar(
            select(PaymentEvent).where(
                PaymentEvent.provider == provider_name,
                PaymentEvent.event_id == result.event_id,
            )
        )

        if existing_event is not None:
            return {
                "status": "already_processed",
                "event_id": result.event_id,
                "provider": provider_name,
            }

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Webhook event could not be processed safely",
        )

    if payment is None:
        event.event_type = "pending_reconciliation"

        db.commit()

        return {
            "status": "pending_reconciliation",
            "event_id": result.event_id,
            "provider": provider_name,
            "message": "Payment not found yet; event stored for reconciliation",
        }

    status_changed = False

    if result.status is not None:
        old_status = payment.status

        apply_payment_status(
            db=db,
            payment=payment,
            new_status=result.status,
            commit=False,
        )

        if result.status.value == "failed":
            payment.failure_reason = (
                payload.get("failure_reason")
                or payload.get("failureReason")
                or payload.get("error")
                or payload.get("message")
                or "Payment failed"
            )

        status_changed = payment.status != old_status

        if (
            result.status.value != old_status
            and not status_changed
        ):
            event.processed = True
            event.processed_at = datetime.now(timezone.utc)

            db.commit()

            return {
                "status": "processed",
                "event_id": result.event_id,
                "provider": provider_name,
                "payment_id": str(payment.id),
                "payment_status": payment.status,
                "status_changed": False,
                "message": (
                    "Webhook received but ignored because "
                    "the requested state transition is not allowed"
                ),
            }

    event.processed = True
    event.processed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(payment)

    return {
        "status": "processed",
        "event_id": result.event_id,
        "provider": provider_name,
        "payment_id": str(payment.id),
        "payment_status": payment.status,
        "status_changed": status_changed,
    }


@router.post(
    "/webhooks/paymob",
)
def paymob_webhook(
    request: Request,
    payload: dict,
    x_paymob_signature: str | None = Header(
        default=None,
        alias="x-paymob-signature",
    ),
    db: Session = Depends(get_db),
):
    return process_webhook(
        provider_name="paymob",
        payload=payload,
        signature=(
            request.query_params.get("hmac")
            or x_paymob_signature
        ),
        db=db,
    )


@router.post(
    "/webhooks/fawry",
)
def fawry_webhook(
    payload: dict,
    x_fawry_signature: str | None = Header(
        default=None,
        alias="x-fawry-signature",
    ),
    db: Session = Depends(get_db),
):
    signature = (
        x_fawry_signature
        or payload.get("signature")
    )

    return process_webhook(
        provider_name="fawry",
        payload=payload,
        signature=signature,
        db=db,
    )


@router.get(
    "/events/{payment_id}",
)
def get_payment_events(
    payment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = db.scalar(
        select(Payment).where(
            Payment.id == payment_id,
            Payment.user_id == current_user.id,
        )
    )

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    events = db.scalars(
        select(PaymentEvent)
        .where(
            PaymentEvent.payment_id == payment.id
        )
        .order_by(
            PaymentEvent.created_at.desc()
        )
    ).all()

    return [
        {
            "id": str(event.id),
            "event_id": event.event_id,
            "provider": event.provider,
            "event_type": event.event_type,
            "payload": event.payload,
            "signature": event.signature,
            "processed": event.processed,
            "processed_at": event.processed_at,
            "created_at": event.created_at,
        }
        for event in events
    ]