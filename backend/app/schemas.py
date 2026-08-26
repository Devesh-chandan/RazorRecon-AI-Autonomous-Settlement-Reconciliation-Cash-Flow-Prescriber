"""Pydantic request/response schemas for all API endpoints."""
from datetime import datetime, date
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field


# ── Recon Run ──────────────────────────────────────────────────────────────────

class ReconRunResponse(BaseModel):
    run_id: str
    status: str
    total_records: Optional[int] = None
    matched_count: Optional[int] = None
    break_count: Optional[int] = None
    match_rate: Optional[float] = None
    net_payout: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReconStatsResponse(BaseModel):
    run_id: str
    total_records: int
    matched_count: int
    break_count: int
    match_rate: float
    net_payout: float
    status: str

    class Config:
        from_attributes = True


# ── Recon Results ──────────────────────────────────────────────────────────────

class ReconResultResponse(BaseModel):
    id: int
    run_id: str
    order_id: str
    settlement_id: Optional[str] = None
    ledger_id: Optional[str] = None
    pass_number: int
    status: str
    confidence: Optional[float] = None
    flags: list[str] = Field(default_factory=list)
    delta: dict[str, Any] = Field(default_factory=dict)
    root_cause: Optional[str] = None
    explanation_en: Optional[str] = None
    explanation_hi: Optional[str] = None
    suggested_action: Optional[str] = None
    severity: Optional[str] = None
    created_at: Optional[datetime] = None
    # Actual transaction amounts — always populated from settlement record
    amount: Optional[float] = None            # gross order amount
    settlement_credit: Optional[float] = None  # net credit after MDR + GST
    # Gateway Performance Matrix fields
    gateway: Optional[str] = None             # HDFC Bank (PG) | ICICI Direct | etc.
    payment_method: Optional[str] = None      # upi | card | netbanking | wallet | emi

    class Config:
        from_attributes = True


# ── Cash Flow ──────────────────────────────────────────────────────────────────

class CashFlowDayResponse(BaseModel):
    date: str
    day_label: str
    confirmed_inflow: float
    disputed_held: float
    projected_total: float


class CashFlowResponse(BaseModel):
    run_id: str
    projection: list[CashFlowDayResponse]
    total_confirmed: float
    total_disputed: float


# ── What-If ───────────────────────────────────────────────────────────────────

class WhatIfRequest(BaseModel):
    run_id: str
    break_order_id: str


class WhatIfDelta(BaseModel):
    date: str
    old_confirmed: float
    new_confirmed: float
    delta: float


class WhatIfResponse(BaseModel):
    resolved_order_id: str
    base_projection: list[CashFlowDayResponse]
    whatif_projection: list[CashFlowDayResponse]
    deltas: list[WhatIfDelta]


# ── Audit Log ─────────────────────────────────────────────────────────────────

class AuditLogEntry(BaseModel):
    id: int
    order_id: str
    settlement_id: Optional[str] = None
    ledger_id: Optional[str] = None
    pass_number: int
    status: str
    confidence: Optional[float] = None
    flags: list[str] = Field(default_factory=list)
    delta: dict[str, Any] = Field(default_factory=dict)
    root_cause: Optional[str] = None
    explanation_en: Optional[str] = None
    explanation_hi: Optional[str] = None
    suggested_action: Optional[str] = None
    severity: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    run_id: str
    total_entries: int
    entries: list[AuditLogEntry]


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    database: dict[str, str]
    redis: dict[str, str]
    groq: dict[str, str]
    version: str = "2.0.0"
