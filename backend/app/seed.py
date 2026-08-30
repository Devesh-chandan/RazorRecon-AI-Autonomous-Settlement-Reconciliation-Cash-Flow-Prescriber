"""
Synthetic data seeder — 100 records mirroring real Indian e-commerce
payment gateway settlement patterns (Razorpay-style).

Generates bounded random data for each run:
- Deterministic order/payment/settlement IDs
- Amounts bounded per category (₹199 .. ₹1,49,999)
- Gateway weights bounded (HDFC, ICICI, Razorpay, Axis, PhonePe)
- Interleaved breaks across a 5-day window so 7-day cashflow ALWAYS includes non-zero disputed holdbacks.
"""
import random
import csv
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

import numpy as np
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine
from app.models import Base, Order, Settlement, ErpLedger

# ── Merchant profile ─────────────────────────────────────────────────────────
MERCHANT = "Trendhive Commerce Pvt Ltd"
MERCHANT_MID = "MID4823099"

GATEWAYS = [
    ("HDFC Bank (PG)",     "HDFC",  35),
    ("ICICI Direct",       "ICIC",  28),
    ("Razorpay Stack",     "RATN",  22),
    ("Axis UPI Express",   "AXIS",  10),
    ("PhonePe Gateway",    "PYTM",   5),
]

GATEWAY_METHOD_WEIGHTS = {
    "HDFC Bank (PG)":    {"card": 0.40, "emi": 0.25, "netbanking": 0.20, "upi": 0.10, "wallet": 0.05},
    "ICICI Direct":      {"card": 0.35, "netbanking": 0.25, "emi": 0.25, "upi": 0.10, "wallet": 0.05},
    "Razorpay Stack":    {"upi": 0.45, "card": 0.25, "wallet": 0.15, "netbanking": 0.10, "emi": 0.05},
    "Axis UPI Express":  {"upi": 0.60, "card": 0.30, "netbanking": 0.05, "wallet": 0.05, "emi": 0.00},
    "PhonePe Gateway":   {"upi": 0.75, "wallet": 0.20, "card": 0.05, "netbanking": 0.00, "emi": 0.00},
}
METHODS = ["upi", "card", "netbanking", "wallet", "emi"]

MDR_RATES = {
    "upi": 0.0,
    "card": 0.020,
    "netbanking": 0.0175,
    "wallet": 0.025,
    "emi": 0.015,
}
GST_RATE = 0.18

CATEGORIES = [
    ("Electronics - Smartphone",    8999,  89999),
    ("Electronics - Laptop",        34999, 149999),
    ("Electronics - Earbuds/TWS",   999,   8999),
    ("Fashion - Men Clothing",      499,   4999),
    ("Fashion - Women Clothing",    799,   7999),
    ("Fashion - Footwear",          999,   5999),
    ("Home & Kitchen",              299,   15999),
    ("Beauty & Personal Care",      199,   3999),
    ("Books & Stationery",          99,    999),
    ("Sports & Fitness",            499,   24999),
    ("Grocery & Essentials",        199,   2999),
    ("Jewellery",                   999,   49999),
]

FIRST_NAMES = [
    "aarav", "vivaan", "aditya", "vihaan", "arjun", "sai", "reyansh", "ayaan",
    "atharv", "dhruv", "ananya", "diya", "saanvi", "riya", "aadhya", "kavya",
    "ishaan", "pranav", "rohit", "priya", "neha", "sneha", "pooja", "akash",
    "rahul", "sunita", "amit", "meera", "harsh", "divya",
]
DOMAINS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "rediffmail.com"]

BASE_DATE = datetime(2026, 8, 1, tzinfo=timezone.utc)


def compute_fee_tax(amount: float, method: str):
    rate = MDR_RATES.get(method, 0.0)
    fee = round(amount * rate, 2)
    tax = round(fee * GST_RATE, 2)
    return fee, tax


def seed(seed_val: Optional[int] = None):
    """Generate bounded random dataset of 100 e-commerce settlement transactions."""
    if seed_val is None:
        seed_val = random.randint(1000, 999999)
    
    print(f"[SEED] Initializing dataset with bounded random seed: {seed_val}")
    rng = np.random.default_rng(seed_val)
    random.seed(seed_val)

    # Build gateway map
    gateway_assignments = []
    for gw_name, utr_pfx, count in GATEWAYS:
        gateway_assignments.extend([(gw_name, utr_pfx)] * count)
    shuffle_idx = rng.permutation(100).tolist()
    gateway_map = [gateway_assignments[shuffle_idx[i]] for i in range(100)]

    from app.database import auto_heal_schema
    Base.metadata.create_all(bind=engine)
    auto_heal_schema(engine)
    db: Session = SessionLocal()


    try:
        db.query(ErpLedger).delete()
        db.query(Settlement).delete()
        db.query(Order).delete()
        db.commit()

        orders, settlements, erp_entries = [], [], []
        csv_settlements_data, csv_erp_data = [], []

        PRODUCT_SAMPLES = {
            "Electronics - Smartphone": ["Redmi Note 13 Pro", "Samsung Galaxy A54 5G", "OnePlus Nord CE3"],
            "Electronics - Laptop": ["Lenovo IdeaPad 3 15\"", "ASUS VivoBook 15", "HP Pavilion x360"],
            "Electronics - Earbuds/TWS": ["Sony WH-1000XM5", "boAt Airdopes 141", "JBL Tune 230NC TWS"],
            "Fashion - Men Clothing": ["Peter England formal shirt", "Jockey innerwear combo", "Levi's 511 jeans"],
            "Fashion - Women Clothing": ["Floral kurti set", "Libas ethnic kurta palazzo", "BIBA printed kurta"],
            "Fashion - Footwear": ["Nike Revolution 6 shoes", "Puma Softride Pro", "Skechers Go Walk 5"],
            "Home & Kitchen": ["Prestige induction cooktop", "Philips air fryer 4L", "Dyson V8 vacuum"],
            "Beauty & Personal Care": ["Lakme 9to5 lipstick set", "Mamaearth vitamin C serum", "Forest Essentials wash"],
            "Books & Stationery": ["UPSC Exam set 2026", "Atomic Habits paperback", "Ikigai paperback"],
            "Sports & Fitness": ["Bowflex adjustable dumbbell", "Boldfit resistance bands", "Yonex badminton racket"],
            "Grocery & Essentials": ["Tata Tea Gold 1kg", "Aashirvaad atta 10kg", "Maggi noodles 12-pack"],
            "Jewellery": ["Tanishq 22K gold mangalsutra", "Malabar diamond pendant", "CaratLane silver anklet"],
        }

        # Interleave 20 break records evenly across indices (every 5th record: 4, 9, 14, 19...)
        # This guarantees break transactions occur across all days in the 7-day projection window!
        break_indices = set(range(4, 100, 5))
        break_list = list(break_indices)
        random.shuffle(break_list)

        # Assign specific break types covering ALL 7 root cause categories across the 20 break records
        missing_erp_set = set(break_list[:4])          # 4 Missing ERP entries
        amount_mismatch_set = set(break_list[4:8])    # 4 Data Entry / Amount mismatches
        disputed_chargeback_set = set(break_list[8:11])# 3 Chargebacks
        mdr_variance_set = set(break_list[11:14])     # 3 Excessive MDR fee variances (>₹30)
        timing_lag_set = set(break_list[14:16])       # 2 Extreme timing lags (>14 days)
        partial_refund_set = set(break_list[16:18])   # 2 Unrecorded partial refunds
        gst_rounding_set = set(break_list[18:])       # 2 GST rounding discrepancies

        # Assign Pass 2 & Pass 3 matched edge cases to non-break indices
        non_break_list = [i for i in range(100) if i not in break_indices]
        random.shuffle(non_break_list)
        pass2_rules_set = set(non_break_list[:10])
        pass3_fuzzy_set = set(non_break_list[10:15])

        for i in range(100):
            cat_idx = int(rng.integers(0, len(CATEGORIES)))
            category_name, lo_price, hi_price = CATEGORIES[cat_idx]

            # Bounded price pick with realistic price points
            base_price = float(rng.integers(lo_price, hi_price))
            amt = round(base_price, 2)

            gateway_name, utr_prefix = gateway_map[i]
            
            # Pick payment method according to gateway distribution
            method_weights = GATEWAY_METHOD_WEIGHTS.get(gateway_name, {m: 0.2 for m in METHODS})
            method = random.choices(list(method_weights.keys()), weights=list(method_weights.values()), k=1)[0]

            fee, tax = compute_fee_tax(amt, method)
            credit = round(amt - fee - tax, 2)

            order_id = f"order_TH2608{i+1:04d}"
            pay_id = f"pay_TH2608{i+1:04d}"
            setl_id = f"setl_TH2608{i+1:04d}"
            led_id = f"LED-TH-2608-{i+1:04d}"
            inv_id = f"INV/2026-27/TH/{i+1:05d}"

            cust_name = random.choice(FIRST_NAMES)
            cust_num = rng.integers(10, 9999)
            customer_email = f"{cust_name}{cust_num}@{random.choice(DOMAINS)}"
            utr = f"{utr_prefix}260826{i+1:06d}00"

            products = PRODUCT_SAMPLES.get(category_name, [category_name])
            product_name = products[i % len(products)]
            erp_product_note = f"{category_name} | {product_name}"

            # Compress order created timestamps to fit inside 4.5 days (1.1 hours per record)
            created = BASE_DATE + timedelta(hours=float(i * 1.1))
            captured = created + timedelta(minutes=float(rng.integers(1, 15)))
            settled = captured + timedelta(days=1)

            order_status = "captured"
            refund_amt = 0.0
            setl_type = "payment"
            setl_debit = 0.0
            erp_status = "received"
            erp_expected = amt
            erp_recorded = amt
            erp_notes = erp_product_note
            skip_erp = False
            setl_credit = credit
            setl_fee = fee
            setl_tax = tax
            setl_amt = amt

            # Apply specific edge-case break & match logic
            if i in pass2_rules_set:
                setl_fee = round(fee + float(rng.uniform(2.50, 4.50)), 2)
                setl_credit = round(amt - setl_fee - tax, 2)
                erp_notes = f"{erp_product_note} | Tier MDR fee variance"

            elif i in pass3_fuzzy_set:
                created = created.replace(hour=23, minute=50)
                captured = created + timedelta(minutes=15)
                settled = captured + timedelta(days=1)
                erp_notes = f"{erp_product_note} | Cross-midnight batch order"

            elif i in missing_erp_set:
                skip_erp = True

            elif i in amount_mismatch_set:
                erp_expected = round(amt + float(rng.uniform(150, 850)), 2)
                erp_recorded = erp_expected
                erp_notes = f"{erp_product_note} | Amount mismatch — ERP invoice typo"

            elif i in disputed_chargeback_set:
                setl_type = "adjustment"
                setl_debit = amt
                setl_credit = -amt
                erp_status = "disputed"
                skip_erp = True
                erp_notes = f"{erp_product_note} | Chargeback holdback dispute"

            elif i in mdr_variance_set:
                setl_fee = round(fee + float(rng.uniform(35.00, 85.00)), 2)
                setl_credit = round(amt - setl_fee - tax, 2)
                erp_notes = f"{erp_product_note} | MDR fee variance exceeding contract rate"

            elif i in timing_lag_set:
                settled = captured + timedelta(days=14)
                erp_notes = f"{erp_product_note} | Severe 14-day settlement delay lag"

            elif i in partial_refund_set:
                order_status = "partial_refund"
                refund_amt = round(amt * 0.35, 2)
                erp_notes = f"{erp_product_note} | Unrecorded partial refund"

            elif i in gst_rounding_set:
                setl_tax = round(tax + 1.85, 2)
                setl_credit = round(amt - fee - setl_tax, 2)
                erp_notes = f"{erp_product_note} | GST tax rounding discrepancy"

            orders.append(Order(
                order_id=order_id,
                payment_id=pay_id,
                amount=Decimal(str(setl_amt)),
                currency="INR",
                status=order_status,
                method=method,
                created_at=created,
                captured_at=captured,
                customer_email=customer_email,
                description=erp_product_note,
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
                settlement_utr=utr,
                settled_at=settled,
                order_id=order_id,
                gateway=gateway_name,
                import_source="seeded",
            ))

            if not skip_erp:
                erp_entries.append(ErpLedger(
                    ledger_id=led_id,
                    invoice_id=inv_id,
                    order_id=order_id,
                    expected_amount=Decimal(str(erp_expected)),
                    recorded_amount=Decimal(str(erp_recorded)),
                    payment_method=method,
                    entry_date=created.date(),
                    status=erp_status,
                    notes=erp_notes,
                ))

        # ── Generate 50 unique CSV records (IDs 101-150, CSV-prefix) ──────────
        # These IDs never overlap with seeded TH records so 0 will be skipped on upload.
        for j in range(101, 151):
            cat_idx = int(rng.integers(0, len(CATEGORIES)))
            category_name, lo_price, hi_price = CATEGORIES[cat_idx]
            base_price = float(rng.integers(lo_price, hi_price))
            csv_amt = round(base_price, 2)
            csv_gw_name, csv_utr_pfx = gateway_map[(j - 1) % len(gateway_map)]
            csv_mw = GATEWAY_METHOD_WEIGHTS.get(csv_gw_name, {m: 0.2 for m in METHODS})
            csv_method = random.choices(list(csv_mw.keys()), weights=list(csv_mw.values()), k=1)[0]
            csv_fee, csv_tax = compute_fee_tax(csv_amt, csv_method)
            csv_credit = round(csv_amt - csv_fee - csv_tax, 2)

            csv_order_id = f"order_CSV2608{j:04d}"
            csv_pay_id   = f"pay_CSV2608{j:04d}"
            csv_setl_id  = f"setl_CSV2608{j:04d}"
            csv_led_id   = f"LED-CSV-{j:04d}"
            csv_inv_id   = f"INV/CSV/{j:05d}"
            csv_utr      = f"{csv_utr_pfx}CSV{j:06d}00"

            csv_created  = BASE_DATE + timedelta(hours=float(j * 1.1))
            csv_settled  = csv_created + timedelta(days=1)

            csv_products = PRODUCT_SAMPLES.get(category_name, [category_name])
            csv_product  = csv_products[j % len(csv_products)]
            csv_note     = f"{category_name} | {csv_product} (CSV Import)"

            csv_settlements_data.append({
                "Settlement ID": csv_setl_id,
                "Entity ID":     csv_pay_id,
                "Type":          "payment",
                "Amount":        f"{csv_amt:.2f}",
                "Fee":           f"{csv_fee:.2f}",
                "Tax":           f"{csv_tax:.2f}",
                "Credit":        f"{csv_credit:.2f}",
                "Debit":         "0.00",
                "Settlement UTR": csv_utr,
                "Settled At":    csv_settled.strftime("%Y-%m-%d %H:%M:%S"),
                "Order ID":      csv_order_id,
                "Gateway":       csv_gw_name,
            })
            csv_erp_data.append({
                "Ledger ID":        csv_led_id,
                "Invoice ID":       csv_inv_id,
                "Order ID":         csv_order_id,
                "Expected Amount":  f"{csv_amt:.2f}",
                "Recorded Amount":  f"{csv_amt:.2f}",
                "Payment Method":   csv_method,
                "Entry Date":       csv_created.date().strftime("%Y-%m-%d"),
                "Status":           "received",
                "Notes":            csv_note,
            })

        db.add_all(orders)
        db.add_all(settlements)
        db.add_all(erp_entries)
        db.commit()

        write_csv_files(csv_settlements_data, csv_erp_data)
        print(f"[OK] Seeded {len(orders)} orders, {len(settlements)} settlements, {len(erp_entries)} ERP entries (seed={seed_val}).")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seed failed: {e}")
        raise
    finally:
        db.close()


def write_csv_files(settlement_rows: list[dict], erp_rows: list[dict]):
    """Write synchronized sample CSV files to samples/ directory."""
    import os
    samples_dir = "../samples"
    os.makedirs(samples_dir, exist_ok=True)
    try:
        with open(os.path.join(samples_dir, "sample_razorpay_settlements.csv"), "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "Settlement ID", "Entity ID", "Type", "Amount", "Fee", "Tax",
                "Credit", "Debit", "Settlement UTR", "Settled At", "Order ID", "Gateway"
            ])
            writer.writeheader()
            writer.writerows(settlement_rows)

        with open(os.path.join(samples_dir, "sample_erp_ledger.csv"), "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "Ledger ID", "Invoice ID", "Order ID", "Expected Amount",
                "Recorded Amount", "Payment Method", "Entry Date", "Status", "Notes"
            ])
            writer.writeheader()
            writer.writerows(erp_rows)

        print("   [CSV] Generated sample_razorpay_settlements.csv & sample_erp_ledger.csv in samples/ directory.")
    except Exception as exc:
        print(f"   [WARN] Failed to write CSV files: {exc}")



if __name__ == "__main__":
    seed()
