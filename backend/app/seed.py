"""
Synthetic data seeder — generates 100 records with all 10 edge case types.
Run: python -m app.seed
"""
import random
import string
from datetime import datetime, timedelta, date, timezone
from decimal import Decimal

import numpy as np
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine
from app.models import Base, Order, Settlement, ErpLedger

# ── Deterministic seed for reproducibility ────────────────────────────────────
SEED = 42
rng = np.random.default_rng(SEED)
random.seed(SEED)

# ── Constants ─────────────────────────────────────────────────────────────────
METHODS = ["upi", "card", "netbanking", "wallet"]
METHOD_WEIGHTS = [0.45, 0.30, 0.15, 0.10]

MDR_RATES = {"upi": 0.0, "card": 0.02, "netbanking": 0.0175, "wallet": 0.025}
GST_RATE = 0.18

BASE_DATE = datetime(2026, 8, 1, tzinfo=timezone.utc)


def rand_id(prefix: str, length: int = 12) -> str:
    chars = string.ascii_letters + string.digits
    suffix = "".join(random.choices(chars, k=length))
    return f"{prefix}{suffix}"


def compute_fee_tax(amount: float, method: str):
    fee = round(amount * MDR_RATES[method], 2)
    tax = round(fee * GST_RATE, 2)
    return fee, tax


def make_order_id(i: int):
    return f"order_Rzp{i:04d}abcd"


def make_payment_id(i: int):
    return f"pay_Rzp{i:04d}efgh"


def make_settlement_id(i: int):
    return f"setl_Rzp{i:04d}ijkl"


def make_ledger_id(i: int):
    return f"LED-2026-{i:04d}"


def make_invoice_id(i: int):
    return f"INV-2026-{i:04d}"


def utc_dt(base: datetime, offset_hours: float = 0) -> datetime:
    return base + timedelta(hours=offset_hours)


# ── Edge case plan ─────────────────────────────────────────────────────────────
# Indices 0-49:  Clean matches
# Indices 50-57: MDR Variance (8)
# Indices 58-67: T+2 Timing Lag (10)
# Indices 68-72: Cross-Midnight (5)
# Indices 73-78: Full Refunds (6)
# Indices 79-82: Partial Refunds (4)
# Indices 83-85: Chargeback Holdbacks (3)
# Indices 86-89: Missing ERP Entry (4)
# Indices 90-91: Duplicate ERP Entry (2)
# Indices 92-96: Amount Mismatch (5)
# Indices 97-99: GST Rounding (3)

def seed():
    print("🌱 Creating tables...")
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # Clear existing data
        db.query(ErpLedger).delete()
        db.query(Settlement).delete()
        db.query(Order).delete()
        db.commit()
        print("🗑️  Cleared existing data.")

        orders = []
        settlements = []
        erp_entries = []

        amounts = [float(round(rng.uniform(199, 9999), 2)) for _ in range(100)]
        methods = rng.choice(METHODS, size=100, p=METHOD_WEIGHTS).tolist()

        for i in range(100):
            amt = amounts[i]
            method = methods[i]
            fee, tax = compute_fee_tax(amt, method)
            credit = round(amt - fee - tax, 2)

            order_id = make_order_id(i)
            pay_id = make_payment_id(i)
            setl_id = make_settlement_id(i)
            led_id = make_ledger_id(i)
            inv_id = make_invoice_id(i)

            created = utc_dt(BASE_DATE, offset_hours=float(rng.integers(0, 240)))
            captured = created + timedelta(minutes=float(rng.integers(1, 30)))
            settled = captured + timedelta(days=1)  # default T+1

            order_status = "captured"
            refund_amt = 0.0
            setl_type = "payment"
            setl_debit = 0.0
            erp_status = "received"
            erp_recorded = amt
            erp_notes = ""
            skip_erp = False
            add_duplicate_erp = False
            setl_credit = credit
            setl_fee = fee
            setl_tax = tax
            setl_amt = amt

            # ── Edge cases ────────────────────────────────────────────────────

            # 50-57: MDR Variance — fee is ±₹0.50–₹5.00 off
            if 50 <= i <= 57:
                variance = round(float(rng.uniform(0.5, 5.0)), 2)
                setl_fee = round(fee + (variance if rng.random() > 0.5 else -variance), 2)
                setl_credit = round(amt - setl_fee - tax, 2)
                erp_notes = "MDR fee discrepancy flagged"

            # 58-67: T+2 Timing Lag
            elif 58 <= i <= 67:
                settled = captured + timedelta(days=2)

            # 68-72: Cross-Midnight — created near midnight
            elif 68 <= i <= 72:
                created = BASE_DATE.replace(hour=23, minute=45) + timedelta(
                    days=int(rng.integers(0, 30))
                )
                captured = created + timedelta(minutes=17)  # crosses midnight
                settled = captured + timedelta(days=1)

            # 73-78: Full Refunds
            elif 73 <= i <= 78:
                order_status = "refunded"
                refund_amt = amt
                setl_type = "refund"
                setl_debit = amt
                setl_credit = 0.0
                setl_fee = 0.0
                setl_tax = 0.0
                erp_status = "received"
                erp_recorded = -amt

            # 79-82: Partial Refunds
            elif 79 <= i <= 82:
                order_status = "partial_refund"
                refund_amt = round(amt * float(rng.uniform(0.2, 0.6)), 2)
                net = round(amt - refund_amt, 2)
                net_fee, net_tax = compute_fee_tax(net, method)
                setl_credit = round(net - net_fee - net_tax, 2)
                erp_recorded = net

            # 83-85: Chargeback Holdbacks
            elif 83 <= i <= 85:
                setl_type = "adjustment"
                setl_debit = amt
                setl_credit = -amt
                erp_status = "disputed"
                skip_erp = True  # no ERP entry expected

            # 86-89: Missing ERP Entry — no erp row
            elif 86 <= i <= 89:
                skip_erp = True

            # 90-91: Duplicate ERP Entry — will add second ERP row
            elif 90 <= i <= 91:
                add_duplicate_erp = True

            # 92-96: Amount Mismatch — data entry typo in ERP
            elif 92 <= i <= 96:
                typo_delta = round(float(rng.uniform(50, 300)), 2)
                erp_recorded = round(amt + typo_delta, 2)

            # 97-99: GST Rounding ₹0.01 discrepancy
            elif 97 <= i <= 99:
                setl_tax = round(tax + 0.01, 2)
                setl_credit = round(amt - setl_fee - setl_tax, 2)

            # ── Build objects ─────────────────────────────────────────────────
            orders.append(Order(
                order_id=order_id,
                payment_id=pay_id,
                amount=Decimal(str(setl_amt)),
                currency="INR",
                status=order_status,
                method=method,
                created_at=created,
                captured_at=captured,
                customer_email=f"user{i}@example.com",
                description=f"Order #{i+1}",
                refund_amount=Decimal(str(refund_amt)),
                erp_invoice=inv_id,
            ))

            settlements.append(Settlement(
                entity_id=pay_id,
                type=setl_type,
                amount=Decimal(str(setl_amt)),
                fee=Decimal(str(setl_fee)),
                tax=Decimal(str(setl_tax)),
                credit=Decimal(str(setl_credit)),
                debit=Decimal(str(setl_debit)),
                settlement_id=setl_id,
                settlement_utr=rand_id("UTR", 16),
                settled_at=settled,
                order_id=order_id,
            ))

            if not skip_erp:
                erp_entries.append(ErpLedger(
                    ledger_id=led_id,
                    invoice_id=inv_id,
                    order_id=order_id,
                    expected_amount=Decimal(str(amt)),
                    recorded_amount=Decimal(str(erp_recorded)),
                    payment_method=method,
                    entry_date=created.date(),
                    status=erp_status,
                    notes=erp_notes,
                ))
                if add_duplicate_erp:
                    erp_entries.append(ErpLedger(
                        ledger_id=f"{led_id}-DUP",
                        invoice_id=inv_id,
                        order_id=order_id,
                        expected_amount=Decimal(str(amt)),
                        recorded_amount=Decimal(str(round(float(rng.uniform(amt * 0.8, amt * 1.2)), 2))),
                        payment_method=method,
                        entry_date=created.date(),
                        status="received",
                        notes="Duplicate entry - suspected data entry error",
                    ))

        db.add_all(orders)
        db.add_all(settlements)
        db.add_all(erp_entries)
        db.commit()

        print(f"✅ Seeded {len(orders)} orders, {len(settlements)} settlements, {len(erp_entries)} ERP entries.")
        print("   Edge case breakdown:")
        print("   • Clean matches:        50")
        print("   • MDR Variance:          8")
        print("   • T+2 Timing Lag:       10")
        print("   • Cross-Midnight:        5")
        print("   • Full Refunds:          6")
        print("   • Partial Refunds:       4")
        print("   • Chargeback Holdbacks:  3")
        print("   • Missing ERP Entry:     4")
        print("   • Duplicate ERP Entry:   2")
        print("   • Amount Mismatch:       5")
        print("   • GST Rounding:          3")

    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
