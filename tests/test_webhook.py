"""Unit tests for Razorpay webhook signature verification.

Run:
    pytest tests/test_webhook.py -v
"""
import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import get_settings

client = TestClient(app)
settings = get_settings()

_TEST_SECRET = "test_webhook_secret_1234"

_PAYMENT_PAYLOAD = {
    "event": "payment.captured",
    "payload": {
        "payment": {
            "entity": {
                "id": "pay_test123456789",
                "order_id": "order_test123456",
                "amount": 100000,
                "currency": "INR",
                "method": "upi",
                "email": "user@test.com",
                "created_at": 1720000000,
                "description": "Test payment",
            }
        }
    },
}

_SETTLEMENT_PAYLOAD = {
    "event": "settlement.processed",
    "payload": {
        "settlement": {
            "entity": {
                "id": "setl_test123456789",
                "entity_id": "pay_test123456789",
                "type": "payment",
                "amount": 99000,
                "fee": 800,
                "tax": 144,
                "credit": 99000,
                "debit": 0,
                "utr": "UTR12345678901234",
                "settled_at": 1720086400,
                "order_id": "order_test123456",
            }
        }
    },
}

_REFUND_PAYLOAD = {
    "event": "refund.processed",
    "payload": {
        "refund": {
            "entity": {
                "id": "rfnd_test123456789",
                "payment_id": "pay_test123456789",
                "amount": 100000,
            }
        }
    },
}


def _make_signature(body: bytes, secret: str) -> str:
    """Compute HMAC-SHA256 signature exactly as Razorpay does."""
    return hmac.new(key=secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256).hexdigest()


def _override_webhook_secret(secret: str):
    """Monkeypatch settings to use a specific webhook secret."""
    import app.routes.ingestion as ing_module
    original = ing_module.settings.RAZORPAY_WEBHOOK_SECRET
    ing_module.settings.RAZORPAY_WEBHOOK_SECRET = secret
    return original


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestWebhookSignatureVerification:

    def test_valid_signature_payment_captured(self):
        """Valid HMAC signature should be accepted (200 OK)."""
        original = _override_webhook_secret(_TEST_SECRET)
        try:
            body = json.dumps(_PAYMENT_PAYLOAD).encode()
            sig = _make_signature(body, _TEST_SECRET)
            response = client.post(
                "/api/webhooks/razorpay",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Razorpay-Signature": sig,
                },
            )
            assert response.status_code == 200, response.text
            data = response.json()
            assert data["status"] == "ok"
            assert data["event"] == "payment.captured"
        finally:
            _override_webhook_secret(original)

    def test_valid_signature_settlement_processed(self):
        """Settlement event with valid signature should return 200."""
        original = _override_webhook_secret(_TEST_SECRET)
        try:
            body = json.dumps(_SETTLEMENT_PAYLOAD).encode()
            sig = _make_signature(body, _TEST_SECRET)
            response = client.post(
                "/api/webhooks/razorpay",
                content=body,
                headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
            )
            assert response.status_code == 200
        finally:
            _override_webhook_secret(original)

    def test_valid_signature_refund_processed(self):
        """Refund event with valid signature should return 200."""
        original = _override_webhook_secret(_TEST_SECRET)
        try:
            body = json.dumps(_REFUND_PAYLOAD).encode()
            sig = _make_signature(body, _TEST_SECRET)
            response = client.post(
                "/api/webhooks/razorpay",
                content=body,
                headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
            )
            assert response.status_code == 200
        finally:
            _override_webhook_secret(original)

    def test_tampered_payload_rejected(self):
        """Modified payload with original signature must be rejected (401)."""
        original = _override_webhook_secret(_TEST_SECRET)
        try:
            body = json.dumps(_PAYMENT_PAYLOAD).encode()
            sig = _make_signature(body, _TEST_SECRET)

            # Tamper: change amount
            tampered = _PAYMENT_PAYLOAD.copy()
            tampered["payload"]["payment"]["entity"]["amount"] = 1  # injected amount
            tampered_body = json.dumps(tampered).encode()

            response = client.post(
                "/api/webhooks/razorpay",
                content=tampered_body,
                headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
            )
            assert response.status_code == 401
        finally:
            _override_webhook_secret(original)

    def test_wrong_secret_rejected(self):
        """Signature generated with wrong secret must be rejected (401)."""
        original = _override_webhook_secret(_TEST_SECRET)
        try:
            body = json.dumps(_PAYMENT_PAYLOAD).encode()
            wrong_sig = _make_signature(body, "wrong_secret")
            response = client.post(
                "/api/webhooks/razorpay",
                content=body,
                headers={"Content-Type": "application/json", "X-Razorpay-Signature": wrong_sig},
            )
            assert response.status_code == 401
        finally:
            _override_webhook_secret(original)

    def test_missing_signature_header(self):
        """Missing X-Razorpay-Signature header must return 422."""
        body = json.dumps(_PAYMENT_PAYLOAD).encode()
        response = client.post(
            "/api/webhooks/razorpay",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422  # FastAPI header validation

    def test_unhandled_event_acknowledged(self):
        """Unrecognised event types should still return 200 (acknowledged & ignored)."""
        original = _override_webhook_secret("")  # dev mode — no signature check
        try:
            payload = {"event": "order.paid", "payload": {}}
            body = json.dumps(payload).encode()
            response = client.post(
                "/api/webhooks/razorpay",
                content=body,
                headers={"Content-Type": "application/json", "X-Razorpay-Signature": "ignored"},
            )
            assert response.status_code == 200
        finally:
            _override_webhook_secret(original)
