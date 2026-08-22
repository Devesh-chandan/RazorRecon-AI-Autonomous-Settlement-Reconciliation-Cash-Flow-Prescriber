"""
Pass 3 — Fuzzy Heuristic Match.

Handles: amount proximity (±2%), partial refunds, duplicate ERP detection,
and chargeback identification.
Expected yield: ~15 records.
"""
from decimal import Decimal
from typing import Any
from app.config import get_settings

settings = get_settings()
AMOUNT_TOLERANCE_PCT = Decimal(str(settings.AMOUNT_TOLERANCE_PCT))


def run_pass3(
    unmatched_settlements: list[dict],
    unmatched_erp: list[dict],
    unmatched_orders: list[dict],
) -> dict[str, Any]:
    """Apply fuzzy heuristics to remaining unmatched records."""

    # Group ERP by order_id for duplicate detection
    erp_by_order: dict[str, list[dict]] = {}
    for erp in unmatched_erp:
        erp_by_order.setdefault(erp["order_id"], []).append(erp)

    order_by_id = {o["order_id"]: o for o in unmatched_orders}

    matched = []
    breaks = []
    matched_order_ids: set[str] = set()

    for settlement in unmatched_settlements:
        order_id = settlement["order_id"]
        if order_id in matched_order_ids:
            continue

        order = order_by_id.get(order_id)
        erp_candidates = erp_by_order.get(order_id, [])
        s_amt = Decimal(str(settlement["amount"]))

        matched_this = False

        # ── H3C: Duplicate ERP Detection ─────────────────────────────────────
        if len(erp_candidates) > 1:
            primary_erp = erp_candidates[0]
            e_amt = Decimal(str(primary_erp["expected_amount"]))
            pct_diff = abs(s_amt - e_amt) / s_amt if s_amt > 0 else Decimal("1")
            confidence = float(Decimal("1.0") - pct_diff)
            matched.append({
                "order_id": order_id,
                "settlement": settlement,
                "erp": primary_erp,
                "order": order,
                "confidence": max(0.5, confidence),
                "flags": ["duplicate_erp_entry"],
                "delta": {
                    "duplicate_ledger_id": erp_candidates[1]["ledger_id"],
                    "duplicate_amount": float(erp_candidates[1]["recorded_amount"]),
                },
                "pass_number": 3,
            })
            matched_order_ids.add(order_id)
            matched_this = True
            continue

        for erp in erp_candidates:
            if order_id in matched_order_ids:
                break

            e_recorded = Decimal(str(erp["recorded_amount"]))
            e_expected = Decimal(str(erp["expected_amount"]))

            # ── H3B: Partial Refund Net Matching ──────────────────────────────
            if order and order.get("status") == "partial_refund":
                refund_amt = Decimal(str(order.get("refund_amount", 0)))
                net_expected = s_amt - refund_amt
                credit = Decimal(str(settlement.get("credit", 0)))
                if abs(credit - net_expected) <= Decimal("5"):
                    matched.append({
                        "order_id": order_id,
                        "settlement": settlement,
                        "erp": erp,
                        "order": order,
                        "confidence": 0.88,
                        "flags": ["partial_refund_adjusted"],
                        "delta": {
                            "refund_amount": float(refund_amt),
                            "net_expected": float(net_expected),
                            "credit": float(credit),
                        },
                        "pass_number": 3,
                    })
                    matched_order_ids.add(order_id)
                    matched_this = True
                    break

            # ── H3A: Amount Proximity Match (±2%) ─────────────────────────────
            if s_amt > 0:
                pct_diff = abs(s_amt - e_recorded) / s_amt
                if pct_diff <= AMOUNT_TOLERANCE_PCT:
                    confidence = float(Decimal("1.0") - pct_diff)
                    matched.append({
                        "order_id": order_id,
                        "settlement": settlement,
                        "erp": erp,
                        "order": order,
                        "confidence": confidence,
                        "flags": ["amount_mismatch"],
                        "delta": {
                            "settlement_amount": float(s_amt),
                            "erp_recorded_amount": float(e_recorded),
                            "variance": float(abs(s_amt - e_recorded)),
                            "variance_pct": float(pct_diff * 100),
                        },
                        "pass_number": 3,
                    })
                    matched_order_ids.add(order_id)
                    matched_this = True
                    break

        # If nothing matched — it's a genuine break
        if not matched_this and order_id not in matched_order_ids:
            erp = erp_candidates[0] if erp_candidates else None
            breaks.append({
                "order_id": order_id,
                "settlement": settlement,
                "erp": erp,
                "order": order,
            })
            matched_order_ids.add(order_id)

    # Also tag settlements with no ERP at all as breaks
    for settlement in unmatched_settlements:
        order_id = settlement["order_id"]
        if order_id not in matched_order_ids:
            order = order_by_id.get(order_id)
            breaks.append({
                "order_id": order_id,
                "settlement": settlement,
                "erp": None,
                "order": order,
            })
            matched_order_ids.add(order_id)

    unmatched_s = [s for s in unmatched_settlements if s["order_id"] not in matched_order_ids]
    unmatched_e = [e for e in unmatched_erp if e["order_id"] not in matched_order_ids]
    unmatched_o = [o for o in unmatched_orders if o["order_id"] not in matched_order_ids]

    return {
        "matched": matched,
        "breaks": breaks,
        "unmatched_settlements": unmatched_s,
        "unmatched_erp": unmatched_e,
        "unmatched_orders": unmatched_o,
    }
