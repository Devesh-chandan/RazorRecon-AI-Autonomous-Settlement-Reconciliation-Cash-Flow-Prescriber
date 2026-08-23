"""Unit tests for multi-pass reconciliation logic (Passes 1-3 rules and fuzzy matching).

Run:
    pytest tests/test_reconcile.py -v
"""
import pytest
from app.engine.pass1_exact import run_pass1
from app.engine.pass2_rules import run_pass2
from app.engine.pass3_fuzzy import run_pass3


class TestMultiPassEnginePipeline:

    def test_pass2_rule_based_contextual_matching(self):
        """Pass 2 should match settlements with GST rounding tolerance."""
        unmatched_settlements = [
            {"order_id": "order_mdr", "amount": 5000.0, "type": "payment", "fee": 100.0, "tax": 18.0, "settlement_id": "setl_mdr"}
        ]
        unmatched_erp = [
            {"order_id": "order_mdr", "expected_amount": 5000.0, "ledger_id": "led_mdr", "payment_method": "upi"}
        ]
        unmatched_orders = [
            {"order_id": "order_mdr", "amount": 5000.0, "status": "captured", "method": "upi"}
        ]

        result = run_pass2(unmatched_settlements, unmatched_erp, unmatched_orders)

        assert len(result["matched"]) == 1
        assert result["matched"][0]["order_id"] == "order_mdr"
        assert result["matched"][0]["pass_number"] == 2

    def test_pass3_fuzzy_matching_detects_breaks(self):
        """Pass 3 should identify breaks for missing ERP records."""
        unmatched_settlements = [
            {"order_id": "order_missing_erp", "amount": 7278.12, "type": "payment", "settlement_id": "setl_break_1"}
        ]
        unmatched_erp = []
        unmatched_orders = [
            {"order_id": "order_missing_erp", "amount": 7278.12, "status": "captured"}
        ]

        result = run_pass3(unmatched_settlements, unmatched_erp, unmatched_orders)

        assert len(result["breaks"]) == 1
        assert result["breaks"][0]["order_id"] == "order_missing_erp"
        assert result["breaks"][0]["erp"] is None

    def test_full_pipeline_pass_progression(self):
        """Test exact matches pass in Pass 1 while breaks proceed to Pass 3."""
        settlements = [
            {"order_id": "order_exact", "amount": 1000.0, "type": "payment", "settlement_id": "setl_1"},
            {"order_id": "order_break", "amount": 2500.0, "type": "payment", "settlement_id": "setl_2"},
        ]
        erp = [
            {"order_id": "order_exact", "expected_amount": 1000.0, "ledger_id": "led_1"},
        ]
        orders = [
            {"order_id": "order_exact", "amount": 1000.0, "status": "captured"},
            {"order_id": "order_break", "amount": 2500.0, "status": "captured"},
        ]

        # Pass 1
        p1 = run_pass1(settlements, erp, orders)
        assert len(p1["matched"]) == 1
        assert p1["matched"][0]["order_id"] == "order_exact"

        # Pass 2
        p2 = run_pass2(p1["unmatched_settlements"], p1["unmatched_erp"], p1["unmatched_orders"])

        # Pass 3
        p3 = run_pass3(p2["unmatched_settlements"], p2["unmatched_erp"], p2["unmatched_orders"])
        assert len(p3["breaks"]) == 1
        assert p3["breaks"][0]["order_id"] == "order_break"
