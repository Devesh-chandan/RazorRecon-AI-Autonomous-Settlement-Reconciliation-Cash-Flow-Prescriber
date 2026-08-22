"""
Cash-Flow Prescriber — 7-day forward projection.

Computes expected inflows per day, accounting for T+1/T+2 settlement
and method-specific MDR rates.
"""
from datetime import datetime, timedelta, timezone, date
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Order, Settlement, ReconResult

settings = get_settings()
MDR_RATES = settings.MDR_RATES
GST_RATE = Decimal("0.18")

# Indian public holidays in 2026 (for T+2 on weekends/holidays)
# Simplified: only Saturday/Sunday are treated as non-settlement days
WEEKEND_DAYS = {5, 6}  # Mon=0 … Sat=5, Sun=6


def _settlement_date(captured_at: datetime) -> date:
    """Return expected settlement date (T+1, skipping weekends)."""
    if captured_at is None:
        return datetime.now(tz=timezone.utc).date()
    d = captured_at.date() if hasattr(captured_at, "date") else captured_at
    # Advance one business day
    settlement = d + timedelta(days=1)
    # If it's a weekend, push to Monday
    while settlement.weekday() in WEEKEND_DAYS:
        settlement += timedelta(days=1)
    return settlement


def _compute_mdr_and_gst(amount: Decimal, method: str) -> tuple[Decimal, Decimal]:
    rate = Decimal(str(MDR_RATES.get(method, 0.02)))
    fee = (amount * rate).quantize(Decimal("0.01"))
    tax = (fee * GST_RATE).quantize(Decimal("0.01"))
    return fee, tax


def get_7day_projection(db: Session, run_id: str) -> list[dict]:
    """
    Build 7-day cash-flow projection from captured orders.

    The window is anchored to the earliest settlement date in the dataset
    (so the chart always shows real data for demo purposes), then falls
    back to today if no data exists.

    Returns a list of 7 dicts:
        { date, confirmed_inflow, disputed_held, projected_total, day_label }
    """
    # Load captured orders that haven't been fully refunded
    orders = db.query(Order).filter(
        Order.status.in_(["captured", "partial_refund"]),
        Order.captured_at != None,
    ).all()

    # Load break order_ids for this run to compute disputed amounts
    break_order_ids: set[str] = set()
    if run_id:
        breaks = db.query(ReconResult).filter(
            ReconResult.run_id == run_id,
            ReconResult.status == "break",
        ).all()
        break_order_ids = {b.order_id for b in breaks}

    # Anchor window: use the earliest settlement date in the dataset
    # This ensures the chart always shows non-zero data for the demo
    if orders:
        settle_dates = [_settlement_date(o.captured_at) for o in orders]
        anchor = min(settle_dates)
    else:
        anchor = datetime.now(tz=timezone.utc).date()

    days = [anchor + timedelta(days=i) for i in range(7)]

    # Build per-day buckets
    confirmed: dict[date, Decimal] = {d: Decimal("0") for d in days}
    disputed: dict[date, Decimal] = {d: Decimal("0") for d in days}

    for order in orders:
        amt = Decimal(str(order.amount))
        refund = Decimal(str(order.refund_amount or 0))
        net_amt = amt - refund
        method = order.method or "card"

        fee, tax = _compute_mdr_and_gst(net_amt, method)
        net_credit = net_amt - fee - tax

        settle_date = _settlement_date(order.captured_at)

        if settle_date in confirmed:
            if order.order_id in break_order_ids:
                disputed[settle_date] += net_credit
            else:
                confirmed[settle_date] += net_credit

    result = []
    for d in days:
        c = float(confirmed[d].quantize(Decimal("0.01")))
        disp = float(disputed[d].quantize(Decimal("0.01")))
        result.append({
            "date": d.isoformat(),
            "day_label": d.strftime("%b %d"),
            "confirmed_inflow": c,
            "disputed_held": disp,
            "projected_total": round(c + disp, 2),
        })

    return result



def what_if_resolve(db: Session, run_id: str, break_order_id: str) -> dict[str, Any]:
    """
    Simulate resolving a break and return the updated 7-day projection.

    The resolved break's amount moves from disputed_held → confirmed_inflow.
    """
    # Get the order details
    order = db.query(Order).filter(Order.order_id == break_order_id).first()
    if not order:
        return {"error": f"Order {break_order_id} not found"}

    # Get base projection (with break still present)
    base = get_7day_projection(db, run_id)

    # Temporarily mark as resolved — recompute without this break in break_order_ids
    breaks = db.query(ReconResult).filter(
        ReconResult.run_id == run_id,
        ReconResult.status == "break",
        ReconResult.order_id != break_order_id,  # exclude the resolved one
    ).all()
    break_order_ids = {b.order_id for b in breaks}

    # Recompute with resolution — same date anchor as get_7day_projection
    all_orders = db.query(Order).filter(
        Order.status.in_(["captured", "partial_refund"]),
        Order.captured_at != None,
    ).all()

    if all_orders:
        settle_dates_anchor = [_settlement_date(o.captured_at) for o in all_orders]
        anchor = min(settle_dates_anchor)
    else:
        anchor = datetime.now(tz=timezone.utc).date()

    days = [anchor + timedelta(days=i) for i in range(7)]

    confirmed: dict[date, Decimal] = {d: Decimal("0") for d in days}
    disputed: dict[date, Decimal] = {d: Decimal("0") for d in days}

    for o in all_orders:

        amt = Decimal(str(o.amount))
        refund = Decimal(str(o.refund_amount or 0))
        net_amt = amt - refund
        method = o.method or "card"
        fee, tax = _compute_mdr_and_gst(net_amt, method)
        net_credit = net_amt - fee - tax
        settle_date = _settlement_date(o.captured_at)

        if settle_date in confirmed:
            if o.order_id in break_order_ids:
                disputed[settle_date] += net_credit
            else:
                confirmed[settle_date] += net_credit

    whatif = []
    for d in days:
        c = float(confirmed[d].quantize(Decimal("0.01")))
        disp = float(disputed[d].quantize(Decimal("0.01")))
        whatif.append({
            "date": d.isoformat(),
            "day_label": d.strftime("%b %d"),
            "confirmed_inflow": c,
            "disputed_held": disp,
            "projected_total": round(c + disp, 2),
        })

    # Compute delta
    deltas = []
    for b, w in zip(base, whatif):
        deltas.append({
            "date": b["date"],
            "old_confirmed": b["confirmed_inflow"],
            "new_confirmed": w["confirmed_inflow"],
            "delta": round(w["confirmed_inflow"] - b["confirmed_inflow"], 2),
        })

    return {
        "resolved_order_id": break_order_id,
        "base_projection": base,
        "whatif_projection": whatif,
        "deltas": deltas,
    }
