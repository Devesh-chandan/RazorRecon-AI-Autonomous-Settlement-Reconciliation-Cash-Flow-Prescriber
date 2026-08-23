"""
Pass 2 — Rule-Based Contextual Match.

Applies 5 rules to unmatched residuals from Pass 1.
Expected yield: ~25 records.
"""
from decimal import Decimal
from datetime import timedelta, datetime
from typing import Any
from app.config import get_settings

settings = get_settings()

MDR_FEE_TOLERANCE = Decimal(str(settings.MDR_FEE_TOLERANCE))
GST_ROUNDING_TOLERANCE = Decimal(str(settings.GST_ROUNDING_TOLERANCE))
SETTLEMENT_WINDOW_DAYS = settings.SETTLEMENT_WINDOW_DAYS
MDR_RATES = settings.MDR_RATES
GST_RATE = Decimal("0.18")


def _expected_mdr(amount: Decimal, method: str) -> Decimal:
    rate = Decimal(str(MDR_RATES.get(method, 0.02)))
    return (amount * rate).quantize(Decimal("0.01"))


def _to_ist_date(dt):
    """Convert a datetime to IST calendar date (UTC+5:30)."""
    if dt is None:
        return None
    from datetime import timezone, timedelta
    IST = timedelta(hours=5, minutes=30)
    if hasattr(dt, "tzinfo") and dt.tzinfo:
        return (dt + IST).date()
    return dt.date()


def run_pass2(
    unmatched_settlements: list[dict],
    unmatched_erp: list[dict],
    unmatched_orders: list[dict],
) -> dict[str, Any]:
    """Apply 5 rules to find matches in residuals."""
    erp_by_order: dict[str, list[dict]] = {}
    for erp in unmatched_erp:
        erp_by_order.setdefault(erp["order_id"], []).append(erp)

    order_by_id = {o["order_id"]: o for o in unmatched_orders}

    matched = []
    matched_order_ids: set[str] = set()

    for settlement in unmatched_settlements:
        order_id = settlement["order_id"]
        if order_id in matched_order_ids:
            continue

        erp_candidates = erp_by_order.get(order_id, [])
        order = order_by_id.get(order_id)
        s_amt = Decimal(str(settlement["amount"]))

        # ── Rule 2E: Full Refund Pairing ─────────────────────────────────────
        if settlement["type"] == "refund":
            if order and order["status"] == "refunded":
                matched.append({
                    "order_id": order_id,
                    "settlement": settlement,
                    "erp": erp_candidates[0] if erp_candidates else None,
                    "order": order,
                    "confidence": 0.97,
                    "flags": ["full_refund"],
                    "delta": {},
                    "pass_number": 2,
                })
                matched_order_ids.add(order_id)
                continue

        # ── Rule 2D: Chargeback/Adjustment ───────────────────────────────────
        if settlement["type"] == "adjustment":
            matched.append({
                "order_id": order_id,
                "settlement": settlement,
                "erp": None,
                "order": order,
                "confidence": 0.90,
                "flags": ["chargeback_holdback"],
                "delta": {"debit": float(settlement.get("debit", 0))},
                "pass_number": 2,
            })
            matched_order_ids.add(order_id)
            continue

        for erp in erp_candidates:
            if order_id in matched_order_ids:
                break

            e_amt = Decimal(str(erp["expected_amount"]))
            flags = []
            confidence = None

            # ── Rule 2A: T+1/T+2 Date Window ────────────────────────────────────
            if order and order.get("captured_at"):
                def _parse_dt(val):
                    """Parse a datetime or ISO string into a datetime object."""
                    if isinstance(val, datetime):
                        return val
                    if isinstance(val, str):
                        try:
                            return datetime.fromisoformat(val.replace("Z", "+00:00"))
                        except Exception:
                            return None
                    return None

                captured_at = _parse_dt(order["captured_at"])
                settled_at = _parse_dt(settlement.get("settled_at"))
                if captured_at and settled_at and s_amt == e_amt:
                    window_end = captured_at + timedelta(days=SETTLEMENT_WINDOW_DAYS)
                    if captured_at <= settled_at <= window_end:
                        flags.append("timing_lag")
                        confidence = 0.95

            # ── Rule 2B: MDR Fee Tolerance ────────────────────────────────────
            if confidence is None and order and s_amt == e_amt:
                method = settlement.get("method") or order.get("method", "card")
                exp_fee = _expected_mdr(s_amt, method)
                actual_fee = Decimal(str(settlement.get("fee", 0)))
                if abs(actual_fee - exp_fee) <= MDR_FEE_TOLERANCE:
                    flags.append("mdr_variance")
                    confidence = 0.93

            # ── Rule 2C: Cross-Midnight Normalization ─────────────────────────
            if confidence is None and order and s_amt == e_amt:
                if order.get("captured_at") and settlement.get("settled_at"):
                    cap_date = _to_ist_date(order["captured_at"])
                    setl_date = _to_ist_date(settlement["settled_at"])
                    if cap_date and setl_date:
                        day_diff = abs((setl_date - cap_date).days)
                        if day_diff <= SETTLEMENT_WINDOW_DAYS:
                            flags.append("cross_midnight")
                            confidence = 0.92

            # ── Rule 2D: GST Rounding Tolerance ──────────────────────────────
            if confidence is None and s_amt == e_amt:
                actual_tax = Decimal(str(settlement.get("tax", 0)))
                actual_fee = Decimal(str(settlement.get("fee", 0)))
                computed_gst = (actual_fee * GST_RATE).quantize(Decimal("0.01"))
                if abs(actual_tax - computed_gst) <= GST_ROUNDING_TOLERANCE:
                    flags.append("gst_rounding")
                    confidence = 0.96

            if confidence is not None:
                matched.append({
                    "order_id": order_id,
                    "settlement": settlement,
                    "erp": erp,
                    "order": order,
                    "confidence": confidence,
                    "flags": flags,
                    "delta": {"fee_variance": float(abs(Decimal(str(settlement.get("fee", 0))) - _expected_mdr(s_amt, order.get("method", "card") if order else "card")))},
                    "pass_number": 2,
                })
                matched_order_ids.add(order_id)

    unmatched_s = [s for s in unmatched_settlements if s["order_id"] not in matched_order_ids]
    unmatched_e = [e for e in unmatched_erp if e["order_id"] not in matched_order_ids]
    unmatched_o = [o for o in unmatched_orders if o["order_id"] not in matched_order_ids]

    return {
        "matched": matched,
        "unmatched_settlements": unmatched_s,
        "unmatched_erp": unmatched_e,
        "unmatched_orders": unmatched_o,
    }
