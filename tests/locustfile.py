"""Locust load test for RazorRecon AI API.

Run:
    locust -f tests/locustfile.py --headless -u 100 -r 10 --run-time 60s --host http://localhost

Or with the web UI:
    locust -f tests/locustfile.py --host http://localhost
    Then open http://localhost:8089
"""
import json
import random
import uuid
from locust import HttpUser, between, task


class ReconUser(HttpUser):
    """Simulates a finance user running reconciliation and viewing results."""

    wait_time = between(0.5, 2)   # seconds between tasks per user

    def on_start(self):
        """Cache a completed run_id for result-fetching tasks."""
        self.run_id = None

    @task(3)
    def trigger_reconciliation(self):
        """POST /api/recon/run — highest weight (most common action)."""
        with self.client.post("/api/recon/run", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                self.run_id = data.get("run_id")
                response.success()
            else:
                response.failure(f"Expected 200, got {response.status_code}")

    @task(5)
    def get_health(self):
        """GET /api/health — lightweight liveness check."""
        self.client.get("/api/health")

    @task(2)
    def get_stats(self):
        """GET /api/recon/stats/<run_id>."""
        if self.run_id:
            self.client.get(f"/api/recon/stats/{self.run_id}")

    @task(1)
    def get_results(self):
        """GET /api/recon/results/<run_id>."""
        if self.run_id:
            self.client.get(f"/api/recon/results/{self.run_id}")

    @task(1)
    def get_cashflow(self):
        """GET /api/cashflow/forecast."""
        self.client.get("/api/cashflow/forecast")


class WebhookStressUser(HttpUser):
    """Simulates Razorpay sending high-frequency webhook events."""

    wait_time = between(0.1, 0.5)

    @task
    def send_payment_webhook(self):
        """POST /api/webhooks/razorpay — payment.captured event (no secret check in dev)."""
        payment_id = f"pay_{uuid.uuid4().hex[:14]}"
        order_id = f"order_{uuid.uuid4().hex[:14]}"
        payload = {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": payment_id,
                        "order_id": order_id,
                        "amount": random.randint(10000, 500000),
                        "currency": "INR",
                        "method": random.choice(["upi", "card", "netbanking", "wallet"]),
                        "email": "test@merchant.com",
                        "created_at": 1720000000,
                        "description": "Load test payment",
                    }
                }
            },
        }
        self.client.post(
            "/api/webhooks/razorpay",
            json=payload,
            headers={"X-Razorpay-Signature": "dev_mode_no_check"},
        )
