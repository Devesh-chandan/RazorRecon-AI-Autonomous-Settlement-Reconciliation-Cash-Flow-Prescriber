"""
Database Reset & Clear Script.
Usage:
    python -m app.reset         # Clears ALL data from database (0 records)
    python -m app.seed          # Resets database back to clean 100 benchmark dataset
"""
import sys
from app.database import SessionLocal, engine
from app.models import Base, Order, Settlement, ErpLedger, ReconRun, ReconResult


def clear_all_data():
    db = SessionLocal()
    try:
        print("[+] Clearing all database records...")
        db.query(ReconResult).delete()
        db.query(ReconRun).delete()
        db.query(ErpLedger).delete()
        db.query(Settlement).delete()
        db.query(Order).delete()
        db.commit()

        total_orders = db.query(Order).count()
        print(f"[SUCCESS] Database cleared! Orders: {total_orders}, Settlements: 0, Recon Runs: 0.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Clear failed: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    clear_all_data()
