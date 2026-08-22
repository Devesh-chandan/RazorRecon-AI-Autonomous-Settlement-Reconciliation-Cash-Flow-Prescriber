"""
Pass 1 — Exact Deterministic Match.

Matches on order_id + amount (exact ₹ match).
Yields ~50 clean records.
"""
from decimal import Decimal
from typing import Any


def run_pass1(
    settlements: list[dict],
    erp_entries: list[dict],
    orders: list[dict],
) -> dict[str, Any]:
    """
    Args:
        settlements: list of settlement dicts from DB
        erp_entries: list of ERP ledger dicts from DB
        orders: list of order dicts from DB

    Returns:
        {
            "matched": [{ order_id, settlement, erp, order, confidence, flags, delta }],
            "unmatched_settlements": [...],
            "unmatched_erp": [...],
            "unmatched_orders": [...],
        }
    """
    # Build lookup maps
    settlement_by_order: dict[str, dict] = {s["order_id"]: s for s in settlements}
    erp_by_order: dict[str, dict] = {}
    for erp in erp_entries:
        oid = erp["order_id"]
        # Only store first occurrence here (duplicates handled in pass 3)
        if oid not in erp_by_order:
            erp_by_order[oid] = erp

    order_by_id: dict[str, dict] = {o["order_id"]: o for o in orders}

    matched = []
    matched_order_ids: set[str] = set()

    for order_id, settlement in settlement_by_order.items():
        erp = erp_by_order.get(order_id)
        order = order_by_id.get(order_id)

        if not erp or not order:
            continue

        # Exact match condition: settlement.amount == erp.expected_amount
        s_amt = Decimal(str(settlement["amount"]))
        e_amt = Decimal(str(erp["expected_amount"]))

        if s_amt == e_amt and settlement["type"] == "payment":
            matched.append({
                "order_id": order_id,
                "settlement": settlement,
                "erp": erp,
                "order": order,
                "confidence": 1.0,
                "flags": [],
                "delta": {},
                "pass_number": 1,
            })
            matched_order_ids.add(order_id)

    unmatched_settlements = [s for s in settlements if s["order_id"] not in matched_order_ids]
    unmatched_erp = [e for e in erp_entries if e["order_id"] not in matched_order_ids]
    unmatched_orders = [o for o in orders if o["order_id"] not in matched_order_ids]

    return {
        "matched": matched,
        "unmatched_settlements": unmatched_settlements,
        "unmatched_erp": unmatched_erp,
        "unmatched_orders": unmatched_orders,
    }
