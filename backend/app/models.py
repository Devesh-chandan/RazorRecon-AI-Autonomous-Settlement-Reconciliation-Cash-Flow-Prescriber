"""SQLAlchemy ORM models for all database tables."""
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Optional, List
from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Date,
    Text, ForeignKey, func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class Order(Base):
    """Internal ERP order records."""
    __tablename__ = "orders"

    id: Any = Column(Integer, primary_key=True, index=True)
    order_id: Any = Column(String(20), unique=True, nullable=False, index=True)
    payment_id: Any = Column(String(20), nullable=False, index=True)
    amount: Any = Column(Numeric(12, 2), nullable=False)
    currency: Any = Column(String(3), default="INR")
    status: Any = Column(String(20), nullable=False)          # captured | refunded | partial_refund
    method: Any = Column(String(20), nullable=False)          # upi | card | netbanking | wallet
    created_at: Any = Column(DateTime(timezone=True), nullable=False)
    captured_at: Any = Column(DateTime(timezone=True))
    customer_email: Any = Column(String(100))
    description: Any = Column(String(255))
    refund_amount: Any = Column(Numeric(12, 2), default=0)
    erp_invoice: Any = Column(String(30))
    created_in_db: Any = Column(DateTime(timezone=True), server_default=func.now())


class Settlement(Base):
    """Razorpay gateway settlement records."""
    __tablename__ = "settlements"

    id: Any = Column(Integer, primary_key=True, index=True)
    entity_id: Any = Column(String(20), nullable=False, index=True)   # maps to payment_id
    type: Any = Column(String(20), nullable=False)                    # payment | refund | adjustment
    amount: Any = Column(Numeric(12, 2), nullable=False)
    fee: Any = Column(Numeric(12, 2), nullable=False)
    tax: Any = Column(Numeric(12, 2), nullable=False)
    credit: Any = Column(Numeric(12, 2), nullable=False)
    debit: Any = Column(Numeric(12, 2), default=0)
    settlement_id: Any = Column(String(20), nullable=False, index=True)
    settlement_utr: Any = Column(String(30))
    settled_at: Any = Column(DateTime(timezone=True), nullable=False)
    order_id: Any = Column(String(20), nullable=False, index=True)
    gateway: Any = Column(String(50))                                 # HDFC Bank (PG) | ICICI Direct | etc.
    import_source: Any = Column(String(20), default='seeded')        # seeded | csv_import | webhook
    created_in_db: Any = Column(DateTime(timezone=True), server_default=func.now())


class ErpLedger(Base):
    """Merchant's internal ERP ledger entries."""
    __tablename__ = "erp_ledger"

    id: Any = Column(Integer, primary_key=True, index=True)
    ledger_id: Any = Column(String(20), unique=True, nullable=False, index=True)
    invoice_id: Any = Column(String(30), nullable=False)
    order_id: Any = Column(String(20), nullable=False, index=True)
    expected_amount: Any = Column(Numeric(12, 2), nullable=False)
    recorded_amount: Any = Column(Numeric(12, 2), nullable=False)
    payment_method: Any = Column(String(20), nullable=False)
    entry_date: Any = Column(Date, nullable=False)
    status: Any = Column(String(20), nullable=False)          # received | pending | disputed
    notes: Any = Column(Text, default="")
    created_in_db: Any = Column(DateTime(timezone=True), server_default=func.now())


class ReconRun(Base):
    """Metadata for each reconciliation run."""
    __tablename__ = "recon_runs"

    id: Any = Column(Integer, primary_key=True, index=True)
    run_id: Any = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    status: Any = Column(String(20), nullable=False, default="running")  # running | complete | error
    total_records: Any = Column(Integer)
    matched_count: Any = Column(Integer)
    break_count: Any = Column(Integer)
    match_rate: Any = Column(Numeric(5, 2))
    net_payout: Any = Column(Numeric(14, 2))
    started_at: Any = Column(DateTime(timezone=True), server_default=func.now())
    completed_at: Any = Column(DateTime(timezone=True))

    results = relationship("ReconResult", back_populates="run", cascade="all, delete-orphan")


class ReconResult(Base):
    """Individual reconciliation result for each record."""
    __tablename__ = "recon_results"

    id: Any = Column(Integer, primary_key=True, index=True)
    run_id: Any = Column(UUID(as_uuid=True), ForeignKey("recon_runs.run_id"), nullable=False, index=True)
    order_id: Any = Column(String(20), nullable=False, index=True)
    settlement_id: Any = Column(String(20))
    ledger_id: Any = Column(String(20))
    pass_number: Any = Column(Integer, nullable=False)        # 1, 2, 3, or 4
    status: Any = Column(String(20), nullable=False)          # matched | break | pending
    confidence: Any = Column(Numeric(3, 2))
    flags: Any = Column(JSONB, default=list)                  # ["mdr_variance", "timing_lag"]
    delta: Any = Column(JSONB, default=dict)                  # {"fee_expected": 99.98, "fee_actual": 102.50}
    root_cause: Any = Column(String(50))                      # mdr_variance | missing_erp | etc.
    explanation_en: Any = Column(Text)
    explanation_hi: Any = Column(Text)
    suggested_action: Any = Column(Text)
    severity: Any = Column(String(10))                        # low | medium | high | critical
    created_at: Any = Column(DateTime(timezone=True), server_default=func.now())

    run = relationship("ReconRun", back_populates="results")
