"""Unit tests for Pass 1 — Exact Deterministic Reconciliation Engine.

Run:
    pytest tests/test_pass1_exact.py -v
"""
import pytest
from app.engine.pass1_exact import run_pass1


class TestPass1ExactMatch:

    def test_pass1_exact_matching(self):
        """Pass 1 should match settlement and ERP entry when order_id and amount match exactly."""
        settlements = [
            {"order_id": "order_001", "amount": 5000.0, "type": "payment", "settlement_id": "setl_001"},
            {"order_id": "order_002", "amount": 10000.0, "type": "payment", "settlement_id": "setl_002"},
        ]
        erp_entries = [
            {"order_id": "order_001", "expected_amount": 5000.0, "ledger_id": "led_001"},
            {"order_id": "order_002", "expected_amount": 10000.0, "ledger_id": "led_002"},
        ]
        orders = [
            {"order_id": "order_001", "amount": 5000.0, "status": "captured"},
            {"order_id": "order_002", "amount": 10000.0, "status": "captured"},
        ]

        result = run_pass1(settlements, erp_entries, orders)

        assert len(result["matched"]) == 2
        assert len(result["unmatched_settlements"]) == 0
        assert result["matched"][0]["confidence"] == 1.0
        assert result["matched"][0]["pass_number"] == 1

    def test_pass1_unmatched_amount_mismatch(self):
        """Settlement with amount mismatch should NOT match in Pass 1."""
        settlements = [
            {"order_id": "order_001", "amount": 4900.0, "type": "payment", "settlement_id": "setl_001"}
        ]
        erp_entries = [
            {"order_id": "order_001", "expected_amount": 5000.0, "ledger_id": "led_001"}
        ]
        orders = [
            {"order_id": "order_001", "amount": 5000.0, "status": "captured"}
        ]

        result = run_pass1(settlements, erp_entries, orders)

        assert len(result["matched"]) == 0
        assert len(result["unmatched_settlements"]) == 1
        assert result["unmatched_settlements"][0]["order_id"] == "order_001"

    def test_pass1_missing_erp_entry(self):
        """Settlement without corresponding ERP entry remains unmatched."""
        settlements = [
            {"order_id": "order_orphan", "amount": 2500.0, "type": "payment", "settlement_id": "setl_999"}
        ]
        erp_entries = []
        orders = [
            {"order_id": "order_orphan", "amount": 2500.0, "status": "captured"}
        ]

        result = run_pass1(settlements, erp_entries, orders)

        assert len(result["matched"]) == 0
        assert len(result["unmatched_settlements"]) == 1
