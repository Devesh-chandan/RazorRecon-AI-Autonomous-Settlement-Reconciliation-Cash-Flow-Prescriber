"""
Bulk Append Seeder — appends N new realistic records WITHOUT clearing existing DB data.
Usage:
    python -m app.seed_append 50      # appends 50 new records
    python -m app.seed_append 200     # appends 200 new records
"""
import sys
import random
import string
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import numpy as np
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine
from app.models import Base, Order, Settlement, ErpLedger

METHODS = ["upi", "card", "netbanking", "wallet"]
METHOD_WEIGHTS = [0.45, 0.30, 0.15, 0.10]
MDR_RATES = {"upi": 0.0, "card": 0.02, "netbanking": 0.0175, "wallet": 0.025}
GST_RATE = 0.18


def rand_id(prefix: str, length: int = 10) -> str:
    chars = string.ascii_letters + string.digits
    suffix = "".join(random.choices(chars, k=length))
    return f"{prefix}_{suffix}"


def append_bulk_data(count: int = 50):
    db: Session = SessionLocal()
    try:
        # Find current highest index to avoid ID collisions
        existing_count = db.query(Order).count()
        start_idx = existing_count + 1000

        print(f"[+] Appending {count} new records to database (starting from ID offset {start_idx})...")

        rng = np.random.default_rng()
        now = datetime.now(timezone.utc)

        orders = []
        settlements = []
        erp_entries = []

        amounts = [float(round(rng.uniform(299, 15000), 2)) for _ in range(count)]
        methods = rng.choice(METHODS, size=count, p=METHOD_WEIGHTS).tolist()

        for i in range(count):
            idx = start_idx + i
            amt = amounts[i]
            method = methods[i]

            fee = round(amt * MDR_RATES[method], 2)
            tax = round(fee * GST_RATE, 2)
            credit = round(amt - fee - tax, 2)

            order_id = f"order_bulk_{idx:05d}"
            pay_id = f"pay_bulk_{idx:05d}"
            setl_id = f"setl_bulk_{idx:05d}"
            led_id = f"LED-BULK-{idx:05d}"
            inv_id = f"INV-BULK-{idx:05d}"

            created = now - timedelta(days=random.randint(0, 10), hours=random.randint(0, 23))
            captured = created + timedelta(minutes=random.randint(1, 45))
            settled = captured + timedelta(days=1)

            orders.append(Order(
                order_id=order_id,
                payment_id=pay_id,
                amount=Decimal(str(amt)),
                currency="INR",
                status="captured",
                method=method,
                created_at=created,
                captured_at=captured,
                customer_email=f"bulk_user_{idx}@merchant.com",
                description=f"Bulk Ingested Order #{idx}",
                refund_amount=Decimal("0.00"),
                erp_invoice=inv_id,
            ))

            settlements.append(Settlement(
                entity_id=pay_id,
                type="payment",
                amount=Decimal(str(amt)),
                fee=Decimal(str(fee)),
                tax=Decimal(str(tax)),
                credit=Decimal(str(credit)),
                debit=Decimal("0.00"),
                settlement_id=setl_id,
                settlement_utr=rand_id("UTR", 14),
                settled_at=settled,
                order_id=order_id,
            ))

            erp_entries.append(ErpLedger(
                ledger_id=led_id,
                invoice_id=inv_id,
                order_id=order_id,
                expected_amount=Decimal(str(amt)),
                recorded_amount=Decimal(str(amt)),
                payment_method=method,
                entry_date=created.date(),
                status="received",
                notes="Bulk data ingest",
            ))

        db.add_all(orders)
        db.add_all(settlements)
        db.add_all(erp_entries)
        db.commit()

        total_orders = db.query(Order).count()
        total_settlements = db.query(Settlement).count()

        print(f"[SUCCESS] Appended {count} records!")
        print(f"          Database total now: {total_orders} Orders, {total_settlements} Settlements.")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Append failed: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    num = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    append_bulk_data(num)
