"""SQLAlchemy ORM models for all database tables."""
import uuid
from datetime import datetime
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

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(20), unique=True, nullable=False, index=True)
    payment_id = Column(String(20), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="INR")
    status = Column(String(20), nullable=False)          # captured | refunded | partial_refund
    method = Column(String(20), nullable=False)          # upi | card | netbanking | wallet
    created_at = Column(DateTime(timezone=True), nullable=False)
    captured_at = Column(DateTime(timezone=True))
    customer_email = Column(String(100))
    description = Column(String(255))
    refund_amount = Column(Numeric(12, 2), default=0)
    erp_invoice = Column(String(30))
    created_in_db = Column(DateTime(timezone=True), server_default=func.now())


class Settlement(Base):
    """Razorpay gateway settlement records."""
    __tablename__ = "settlements"

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(String(20), nullable=False, index=True)   # maps to payment_id
    type = Column(String(20), nullable=False)                    # payment | refund | adjustment
    amount = Column(Numeric(12, 2), nullable=False)
    fee = Column(Numeric(12, 2), nullable=False)
    tax = Column(Numeric(12, 2), nullable=False)
    credit = Column(Numeric(12, 2), nullable=False)
    debit = Column(Numeric(12, 2), default=0)
    settlement_id = Column(String(20), nullable=False, index=True)
    settlement_utr = Column(String(30))
    settled_at = Column(DateTime(timezone=True), nullable=False)
    order_id = Column(String(20), nullable=False, index=True)
    created_in_db = Column(DateTime(timezone=True), server_default=func.now())


class ErpLedger(Base):
    """Merchant's internal ERP ledger entries."""
    __tablename__ = "erp_ledger"

    id = Column(Integer, primary_key=True, index=True)
    ledger_id = Column(String(20), unique=True, nullable=False, index=True)
    invoice_id = Column(String(30), nullable=False)
    order_id = Column(String(20), nullable=False, index=True)
    expected_amount = Column(Numeric(12, 2), nullable=False)
    recorded_amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(String(20), nullable=False)
    entry_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False)          # received | pending | disputed
    notes = Column(Text, default="")
    created_in_db = Column(DateTime(timezone=True), server_default=func.now())


class ReconRun(Base):
    """Metadata for each reconciliation run."""
    __tablename__ = "recon_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    status = Column(String(20), nullable=False, default="running")  # running | complete | error
    total_records = Column(Integer)
    matched_count = Column(Integer)
    break_count = Column(Integer)
    match_rate = Column(Numeric(5, 2))
    net_payout = Column(Numeric(14, 2))
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    results = relationship("ReconResult", back_populates="run", cascade="all, delete-orphan")


class ReconResult(Base):
    """Individual reconciliation result for each record."""
    __tablename__ = "recon_results"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(UUID(as_uuid=True), ForeignKey("recon_runs.run_id"), nullable=False, index=True)
    order_id = Column(String(20), nullable=False, index=True)
    settlement_id = Column(String(20))
    ledger_id = Column(String(20))
    pass_number = Column(Integer, nullable=False)        # 1, 2, 3, or 4
    status = Column(String(20), nullable=False)          # matched | break | pending
    confidence = Column(Numeric(3, 2))
    flags = Column(JSONB, default=list)                  # ["mdr_variance", "timing_lag"]
    delta = Column(JSONB, default=dict)                  # {"fee_expected": 99.98, "fee_actual": 102.50}
    root_cause = Column(String(50))                      # mdr_variance | missing_erp | etc.
    explanation_en = Column(Text)
    explanation_hi = Column(Text)
    suggested_action = Column(Text)
    severity = Column(String(10))                        # low | medium | high | critical
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    run = relationship("ReconRun", back_populates="results")
