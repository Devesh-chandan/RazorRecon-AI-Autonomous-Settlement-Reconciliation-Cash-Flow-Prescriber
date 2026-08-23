"""
Send Test Webhook Script — fires live HMAC-SHA256 signed payment.captured
and settlement.processed events to your ngrok endpoint.
Usage:
    python -m app.send_test_webhook
"""
import json
import hashlib
import hmac
import requests
import uuid
from datetime import datetime, timezone

# Target ngrok URL
NGROK_URL = "https://pursuit-parcel-coat.ngrok-free.dev/api/webhooks/razorpay"
SECRET = "rzp_whsec_9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c"


def send_event(event_name: str, payload_entity: dict):
    body = {
        "event": event_name,
        "payload": payload_entity
    }
    body_bytes = json.dumps(body, separators=(',', ':')).encode("utf-8")

    # Compute HMAC-SHA256 signature
    signature = hmac.new(
        key=SECRET.encode("utf-8"),
        msg=body_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "X-Razorpay-Signature": signature
    }

    print(f"[+] Sending '{event_name}' to {NGROK_URL}...")
    try:
        res = requests.post(NGROK_URL, data=body_bytes, headers=headers, timeout=10)
        print(f"[RESPONSE] Status {res.status_code}: {res.text}")
    except Exception as e:
        print(f"[ERROR] Failed to send webhook: {e}")


def main():
    order_id = f"order_live_{uuid.uuid4().hex[:8]}"
    pay_id = f"pay_live_{uuid.uuid4().hex[:8]}"
    setl_id = f"setl_live_{uuid.uuid4().hex[:8]}"

    # 1. Fire payment.captured
    payment_payload = {
        "payment": {
            "entity": {
                "id": pay_id,
                "order_id": order_id,
                "amount": 250000,   # ₹2,500.00
                "currency": "INR",
                "method": "upi",
                "email": "live_test_user@merchant.com",
                "created_at": int(datetime.now(timezone.utc).timestamp()),
                "description": "Live Webhook Simulation Test"
            }
        }
    }
    send_event("payment.captured", payment_payload)

    # 2. Fire settlement.processed
    settlement_payload = {
        "settlement": {
            "entity": {
                "id": setl_id,
                "entity_id": pay_id,
                "type": "payment",
                "amount": 250000,
                "fee": 500,        # ₹5.00
                "tax": 90,         # ₹0.90
                "credit": 249410,  # ₹2,494.10
                "debit": 0,
                "utr": f"UTR{uuid.uuid4().hex[:10].upper()}",
                "settled_at": int(datetime.now(timezone.utc).timestamp()),
                "order_id": order_id
            }
        }
    }
    send_event("settlement.processed", settlement_payload)


if __name__ == "__main__":
    main()
