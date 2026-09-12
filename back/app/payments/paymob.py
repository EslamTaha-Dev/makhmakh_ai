import hashlib
import hmac
from decimal import Decimal
from typing import Any

import httpx

from app.core.config import get_settings
from app.payments.provider import PaymentProvider
from app.payments.types import (
    CheckoutSession,
    PaymentRequest,
    PaymentStatus,
    WebhookResult,
)


class PaymobProvider(PaymentProvider):
    name = "paymob"

    def __init__(self):
        settings = get_settings()

        self.base_url = settings.paymob_base_url.rstrip("/")
        self.api_key = settings.paymob_api_key
        self.hmac_secret = settings.paymob_hmac_secret
        self.checkout_url = settings.paymob_checkout_url
        self.timeout = settings.payment_request_timeout_seconds

    def _headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

    def _validate_configuration(self) -> None:
        if not self.base_url:
            raise RuntimeError(
                "Paymob base URL is not configured"
            )

        if not self.api_key:
            raise RuntimeError(
                "Paymob API key is not configured"
            )

    def create_checkout(
        self,
        request: PaymentRequest,
    ) -> CheckoutSession:
        self._validate_configuration()

        payload = {
            "amount": str(request.amount),
            "currency": request.currency,
            "order_id": request.order_id,
            "customer": {
                "name": request.customer.name,
                "email": request.customer.email,
                "phone": request.customer.phone,
            },
            "callback_url": request.callback_url,
            "metadata": request.metadata or {},
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.base_url,
                    json=payload,
                    headers=self._headers(),
                )

            response.raise_for_status()

        except httpx.TimeoutException as exc:
            raise RuntimeError(
                "Paymob request timed out"
            ) from exc

        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Paymob returned HTTP {exc.response.status_code}"
            ) from exc

        except httpx.RequestError as exc:
            raise RuntimeError(
                "Unable to connect to Paymob"
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(
                "Paymob returned an invalid JSON response"
            ) from exc

        if not isinstance(data, dict):
            raise RuntimeError(
                "Paymob returned an invalid response format"
            )

        external_id = str(
            data.get("id")
            or data.get("order_id")
            or data.get("payment_id")
            or request.order_id
        )

        checkout_url = (
            data.get("checkout_url")
            or data.get("url")
            or self.checkout_url
        )

        return CheckoutSession(
            provider=self.name,
            external_id=external_id,
            checkout_url=checkout_url,
            status=PaymentStatus.PROCESSING,
            raw_response=data,
        )

    def verify_webhook(
        self,
        payload: dict[str, Any],
        signature: str | None,
    ) -> WebhookResult:
        if not self.hmac_secret:
            raise RuntimeError(
                "Paymob HMAC secret is not configured"
            )

        if not signature:
            raise ValueError(
                "Missing Paymob webhook signature"
            )

        calculated_signature = self._calculate_hmac(payload)

        if not hmac.compare_digest(
            calculated_signature.lower(),
            signature.strip().lower(),
        ):
            raise ValueError(
                "Invalid Paymob webhook signature"
            )

        event_id = str(
            payload.get("id")
            or payload.get("event_id")
            or payload.get("transaction_id")
            or ""
        ).strip()

        if not event_id:
            raise ValueError(
                "Paymob webhook does not contain an event identifier"
            )

        external_id = None

        if payload.get("transaction_id") is not None:
            external_id = str(
                payload["transaction_id"]
            )
        elif payload.get("id") is not None:
            external_id = str(
                payload["id"]
            )

        event_type = str(
            payload.get("type")
            or payload.get("event_type")
            or "payment.updated"
        )

        success = payload.get("success")

        if success is True:
            payment_status = PaymentStatus.PAID
        elif success is False:
            payment_status = PaymentStatus.FAILED
        else:
            payment_status = None

        return WebhookResult(
            event_id=event_id,
            event_type=event_type,
            external_id=external_id,
            status=payment_status,
            payload=payload,
            signature=signature,
        )

    def _calculate_hmac(
        self,
        payload: dict[str, Any],
    ) -> str:
        source_data = payload.get("source_data")

        if not isinstance(source_data, dict):
            source_data = {}

        ordered_values = [
            payload.get("amount_cents"),
            payload.get("created_at"),
            payload.get("currency"),
            payload.get("error_occured"),
            payload.get("has_parent_transaction"),
            payload.get("id"),
            payload.get("integration_id"),
            payload.get("is_3d_secure"),
            payload.get("is_auth"),
            payload.get("is_capture"),
            payload.get("is_refunded"),
            payload.get("is_standalone_payment"),
            payload.get("is_voided"),
            payload.get("order"),
            payload.get("owner"),
            payload.get("pending"),
            source_data.get("pan"),
            source_data.get("sub_type"),
            source_data.get("type"),
            payload.get("success"),
        ]

        message = "".join(
            str(value) if value is not None else ""
            for value in ordered_values
        )

        return hmac.new(
            self.hmac_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha512,
        ).hexdigest()

    def get_payment_status(
        self,
        external_id: str,
    ) -> str:
        self._validate_configuration()

        if not external_id:
            raise ValueError(
                "Paymob external payment ID is required"
            )

        url = f"{self.base_url}/{external_id}"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    url,
                    headers=self._headers(),
                )

            response.raise_for_status()

        except httpx.TimeoutException as exc:
            raise RuntimeError(
                "Paymob status request timed out"
            ) from exc

        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Paymob returned HTTP {exc.response.status_code}"
            ) from exc

        except httpx.RequestError as exc:
            raise RuntimeError(
                "Unable to connect to Paymob"
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(
                "Paymob returned an invalid JSON response"
            ) from exc

        if not isinstance(data, dict):
            raise RuntimeError(
                "Paymob returned an invalid response format"
            )

        return str(
            data.get("status")
            or data.get("state")
            or "unknown"
        )

    def refund_payment(
        self,
        external_id: str,
        amount: Decimal | None = None,
    ) -> bool:
        self._validate_configuration()

        if not external_id:
            raise ValueError(
                "Paymob external payment ID is required"
            )

        payload: dict[str, Any] = {
            "external_id": external_id,
        }

        if amount is not None:
            payload["amount"] = str(amount)

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/refunds",
                    json=payload,
                    headers=self._headers(),
                )

            response.raise_for_status()

        except httpx.TimeoutException as exc:
            raise RuntimeError(
                "Paymob refund request timed out"
            ) from exc

        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Paymob refund request returned HTTP {exc.response.status_code}"
            ) from exc

        except httpx.RequestError as exc:
            raise RuntimeError(
                "Unable to connect to Paymob for refund"
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(
                "Paymob returned an invalid JSON response"
            ) from exc

        if not isinstance(data, dict):
            raise RuntimeError(
                "Paymob returned an invalid refund response format"
            )

        success = data.get("success")
        if isinstance(success, bool):
            return success

        status = str(
            data.get("status")
            or data.get("state")
            or ""
        ).strip().lower()

        return status in {
            "success",
            "succeeded",
            "paid",
            "refunded",
            "approved",
            "completed",
        }