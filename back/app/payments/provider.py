from abc import ABC, abstractmethod
from app.payments.types import (
    CheckoutSession,
    PaymentRequest,
    WebhookResult,
)

class PaymentProvider(ABC):
    name: str

    @abstractmethod
    def create_checkout(
        self,
        request: PaymentRequest,
    ) -> CheckoutSession:
        raise NotImplementedError

    @abstractmethod
    def verify_webhook(
        self,
        payload: dict,
        signature: str | None,
    ) -> WebhookResult:
        raise NotImplementedError

    @abstractmethod
    def get_payment_status(
        self,
        external_id: str,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def refund_payment(
        self,
        external_id: str,
        amount=None,
    ) -> bool:
        raise NotImplementedError