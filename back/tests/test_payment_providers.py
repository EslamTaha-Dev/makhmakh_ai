import hashlib
import hmac

from app.payments.fawry import FawryProvider
from app.payments.paymob import PaymobProvider


def test_paymob_hmac_uses_nested_transaction_fields():
    provider = PaymobProvider.__new__(PaymobProvider)
    provider.hmac_secret = "secret"
    transaction = {
        "amount_cents": 1000,
        "created_at": "2026-09-13T00:00:00Z",
        "currency": "EGP",
        "id": 42,
        "order": {"id": 99},
        "pending": False,
        "source_data": {
            "pan": "1234",
            "sub_type": "Visa",
            "type": "card",
        },
        "success": True,
    }

    message = (
        "10002026-09-13T00:00:00ZEGP42"
        "99false1234Visacardtrue"
    )
    expected = hmac.new(
        b"secret",
        message.encode(),
        hashlib.sha512,
    ).hexdigest()

    assert provider._calculate_hmac({"obj": transaction}) == expected


def test_fawry_webhook_signature_uses_official_fields():
    provider = FawryProvider.__new__(FawryProvider)
    provider.security_key = "secret"
    payload = {
        "requestId": "request-1",
        "fawryRefNumber": "fawry-1",
        "merchantRefNumber": "merchant-1",
        "paymentAmount": "100.00",
        "orderStatus": "PAID",
    }

    expected = hashlib.sha256(
        b"request-1fawry-1merchant-1100.00PAIDsecret"
    ).hexdigest()

    assert provider._webhook_signature(payload) == expected
