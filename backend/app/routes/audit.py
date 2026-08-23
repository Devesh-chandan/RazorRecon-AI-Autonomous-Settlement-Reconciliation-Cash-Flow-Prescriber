"""Audit log API routes."""
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ReconResult, ReconRun
from app.schemas import AuditLogEntry, AuditLogResponse

router = APIRouter(prefix="/api/audit", tags=["audit"])
logger = logging.getLogger(__name__)


@router.get("/{run_id}", response_model=AuditLogResponse)
async def get_audit_log(run_id: str, pass_number: Optional[int] = None, status: Optional[str] = None, db: Session = Depends(get_db)):
    """Full audit log for a reconciliation run."""
    recon_run = db.query(ReconRun).filter(ReconRun.run_id == run_id).first()
    if not recon_run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    query = db.query(ReconResult).filter(ReconResult.run_id == run_id)
    if pass_number is not None:
        query = query.filter(ReconResult.pass_number == pass_number)
    if status is not None:
        query = query.filter(ReconResult.status == status)

    results = query.order_by(ReconResult.pass_number, ReconResult.id).all()

    entries = [
        AuditLogEntry(
            id=r.id,
            order_id=r.order_id,
            settlement_id=r.settlement_id,
            ledger_id=r.ledger_id,
            pass_number=r.pass_number,
            status=r.status,
            confidence=float(r.confidence) if r.confidence else None,
            flags=r.flags or [],
            delta=r.delta or {},
            root_cause=r.root_cause,
            explanation_en=r.explanation_en,
            explanation_hi=r.explanation_hi,
            suggested_action=r.suggested_action,
            severity=r.severity,
            created_at=r.created_at,
        )
        for r in results
    ]

    return AuditLogResponse(
        run_id=run_id,
        total_entries=len(entries),
        entries=entries,
    )


@router.get("/{run_id}/export")
async def export_audit_log(run_id: str, db: Session = Depends(get_db)):
    """Download full audit log as a JSON file."""
    recon_run = db.query(ReconRun).filter(ReconRun.run_id == run_id).first()
    if not recon_run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    results = db.query(ReconResult).filter(ReconResult.run_id == run_id).order_by(ReconResult.pass_number, ReconResult.id).all()

    export_data = {
        "run_id": run_id,
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "summary": {
            "total_records": recon_run.total_records,
            "matched_count": recon_run.matched_count,
            "break_count": recon_run.break_count,
            "match_rate": float(recon_run.match_rate) if recon_run.match_rate else None,
            "net_payout": float(recon_run.net_payout) if recon_run.net_payout else None,
        },
        "entries": [
            {
                "id": r.id,
                "order_id": r.order_id,
                "settlement_id": r.settlement_id,
                "ledger_id": r.ledger_id,
                "pass_number": r.pass_number,
                "status": r.status,
                "confidence": float(r.confidence) if r.confidence else None,
                "flags": r.flags or [],
                "delta": r.delta or {},
                "root_cause": r.root_cause,
                "explanation_en": r.explanation_en,
                "explanation_hi": r.explanation_hi,
                "suggested_action": r.suggested_action,
                "severity": r.severity,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in results
        ],
    }

    filename = f"razorrecon_audit_{run_id[:8]}.json"
    return Response(
        content=json.dumps(export_data, indent=2, ensure_ascii=False),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
