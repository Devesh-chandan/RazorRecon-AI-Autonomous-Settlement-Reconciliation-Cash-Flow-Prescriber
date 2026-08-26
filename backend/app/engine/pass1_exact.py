"""
Pass 1 — Exact Deterministic Match.

Matches on order_id + amount (exact ₹ match).
Yields ~50 clean records.
"""
from decimal import Decimal
from typing import Any
from app.config import get_settings

settings = get_settings()
MDR_RATES = settings.MDR_RATES


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

        # Exact match condition: settlement.amount == erp.expected_amount == erp.recorded_amount
        s_amt = Decimal(str(settlement["amount"]))
        e_amt = Decimal(str(erp["expected_amount"]))
        r_amt = Decimal(str(erp.get("recorded_amount", erp["expected_amount"])))

        # Verify MDR fee consistency (fee difference <= 0.05)
        s_fee = Decimal(str(settlement.get("fee", 0)))
        method = settlement.get("method") or (order.get("method") if order else "card")
        mdr_rate = Decimal(str(MDR_RATES.get(method, 0.0)))
        exp_fee = (s_amt * mdr_rate).quantize(Decimal("0.01"))
        fee_clean = abs(s_fee - exp_fee) <= Decimal("0.05")

        if s_amt == e_amt and s_amt == r_amt and fee_clean and settlement["type"] == "payment":
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
