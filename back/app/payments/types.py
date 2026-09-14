from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    AUTHORIZED = "authorized"
    PAID = "paid"
    FAILED = "failed"
    CANCELED = "canceled"
    EXPIRED = "expired"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    PENDING_RECONCILIATION = "pending_reconciliation"


class SubscriptionStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELED = "canceled"


@dataclass
class CustomerInfo:
    name: str
    email: str
    phone: str | None = None


@dataclass
class CheckoutSession:
    provider: str
    external_id: str
    checkout_url: str | None
    status: PaymentStatus
    raw_response: dict[str, Any]


@dataclass
class WebhookResult:
    event_id: str
    event_type: str
    external_id: str | None
    status: PaymentStatus | None
    payload: dict[str, Any]
    signature: str | None = None


@dataclass
class PaymentRequest:
    amount: Decimal
    currency: str
    order_id: str
    customer: CustomerInfo
    callback_url: str | None = None
    metadata: dict[str, Any] | None = None