import hashlib
import json
from decimal import Decimal
from typing import Any

import requests

from app.core.config import get_settings
from app.payments.provider import PaymentProvider
from app.payments.types import (
    CheckoutSession,
    CustomerInfo,
    PaymentRequest,
    PaymentStatus,
    WebhookResult,
)


class FawryProvider(PaymentProvider):
    name = "fawry"

    def __init__(self) -> None:
        self.settings = get_settings()

        if not self.settings.fawry_base_url:
            raise RuntimeError(
                "Fawry base URL is not configured"
            )

        self.base_url = self.settings.fawry_base_url.rstrip("/")

        self.merchant_code = (
            self.settings.fawry_merchant_code.strip()
        )

        self.security_key = (
            self.settings.fawry_security_key.strip()
        )

    def _generate_signature(
        self,
        values: list[Any],
    ) -> str:
        raw = "".join(
            str(value)
            for value in values
            if value is not None
        )

        raw += self.security_key

        return hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()

    def _webhook_signature(self, payload: dict) -> str:
        values = [
            payload.get("requestId"),
            payload.get("fawryRefNumber"),
            payload.get("merchantRefNumber"),
            payload.get("paymentAmount"),
            payload.get("orderStatus"),
        ]

        return self._generate_signature(values)

    def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict:
        url = f"{self.base_url}/{path.lstrip('/')}"

        timeout = self.settings.payment_request_timeout_seconds

        try:
            response = requests.request(
                method=method,
                url=url,
                timeout=timeout,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise RuntimeError(
                "Fawry service is unavailable"
            ) from exc

        try:
            data = response.json()
        except ValueError:
            data = {
                "raw_response": response.text
            }

        if not response.ok:
            raise RuntimeError(
                f"Fawry request failed with status "
                f"{response.status_code}"
            )

        if isinstance(data, dict):
            return data

        return {
            "data": data
        }

    def create_checkout(
        self,
        request: PaymentRequest,
    ) -> CheckoutSession:

        customer: CustomerInfo = request.customer

        amount = Decimal(request.amount).quantize(
            Decimal("0.01")
        )

        merchant_ref_num = request.order_id

        signature = self._generate_signature(
            [
                self.merchant_code,
                merchant_ref_num,
                amount,
                request.currency,
                customer.email,
                customer.phone,
            ]
        )

        payload = {
            "merchantCode": self.merchant_code,
            "merchantRefNum": merchant_ref_num,
            "customerProfileId": customer.email,
            "customerName": customer.name,
            "customerEmail": customer.email,
            "customerMobile": customer.phone,
            "amount": float(amount),
            "currencyCode": request.currency,
            "language": "en-gb",
            "chargeItems": [],
            "signature": signature,
        }

        if request.metadata:
            payload["metadata"] = request.metadata

        response = self._request(
            "POST",
            "/payments",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

        external_id = (
            response.get("referenceNumber")
            or response.get("merchantRefNum")
            or response.get("fawryRefNumber")
            or merchant_ref_num
        )

        checkout_url = (
            response.get("paymentUrl")
            or response.get("checkoutUrl")
            or response.get("url")
        )

        response_status = str(
            response.get("statusCode")
            or response.get("status")
            or "200"
        ).lower()

        if response_status in {
            "200",
            "201",
            "success",
            "successful",
            "paid",
        }:
            payment_status = PaymentStatus.PENDING
        else:
            payment_status = PaymentStatus.FAILED

        return CheckoutSession(
            provider=self.name,
            external_id=str(external_id),
            checkout_url=checkout_url,
            status=payment_status,
            raw_response=response,
        )

    def verify_webhook(
        self,
        payload: dict,
        signature: str | None,
    ) -> WebhookResult:

        received_signature = (
            signature
            or payload.get("signature")
        )

        if not received_signature:
            raise ValueError(
                "Fawry webhook signature is required"
            )

        event_id = (
            payload.get("event_id")
            or payload.get("eventId")
            or payload.get("referenceNumber")
            or payload.get("merchantRefNum")
        )

        if not event_id:
            raise ValueError(
                "Fawry webhook event ID is required"
            )

        external_id = (
            payload.get("referenceNumber")
            or payload.get("fawryRefNumber")
            or payload.get("merchantRefNum")
        )

        event_type = str(
            payload.get("event_type")
            or payload.get("eventType")
            or payload.get("status")
            or "payment_update"
        )

        status_value = str(
            payload.get("status")
            or payload.get("paymentStatus")
            or payload.get("orderStatus")
            or ""
        ).lower()

        if status_value in {
            "paid",
            "success",
            "successful",
            "completed",
            "captured",
            "200",
        }:
            payment_status = PaymentStatus.PAID

        elif status_value in {
            "failed",
            "failure",
            "rejected",
            "declined",
            "cancelled",
            "canceled",
        }:
            if status_value in {
                "cancelled",
                "canceled",
            }:
                payment_status = PaymentStatus.CANCELED
            else:
                payment_status = PaymentStatus.FAILED

        elif status_value in {
            "processing",
            "pending",
            "initiated",
            "in_progress",
        }:
            payment_status = PaymentStatus.PROCESSING

        else:
            payment_status = None

        if {
            "requestId",
            "fawryRefNumber",
            "merchantRefNumber",
            "paymentAmount",
            "orderStatus",
        }.issubset(payload):
            expected_signature = self._webhook_signature(
                payload
            )
        else:
            expected_signature = self._generate_signature(
                [
                    external_id,
                    payload.get("status"),
                    payload.get("amount"),
                ]
            )

        if (
            not self.security_key
            or received_signature.lower()
            != expected_signature.lower()
        ):
            raise ValueError(
                "Invalid Fawry webhook signature"
            )

        return WebhookResult(
            event_id=str(event_id),
            event_type=event_type,
            external_id=(
                str(external_id)
                if external_id is not None
                else None
            ),
            status=payment_status,
            payload=payload,
        )

    def get_payment_status(
        self,
        external_id: str,
    ) -> str:
        if not external_id:
            raise ValueError(
                "Fawry payment reference is required"
            )

        response = self._request(
            "GET",
            f"/payments/{external_id}",
        )

        return str(
            response.get("orderStatus")
            or response.get("paymentStatus")
            or response.get("status")
            or "unknown"
        )

    def refund_payment(
        self,
        external_id: str,
        amount: Decimal | None = None,
    ) -> bool:
        if not external_id:
            raise ValueError(
                "Fawry payment reference is required"
            )

        payload = {
            "merchantCode": self.merchant_code,
            "referenceNumber": external_id,
        }

        if amount is not None:
            payload["refundAmount"] = float(amount)

        response = self._request(
            "POST",
            "/payments/refund",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

        status_value = str(
            response.get("status")
            or response.get("orderStatus")
            or response.get("statusCode")
            or ""
        ).lower()

        return status_value in {
            "200",
            "success",
            "successful",
            "refunded",
        }