"""Cash-flow projection API routes."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import CashFlowResponse, CashFlowDayResponse, WhatIfRequest, WhatIfResponse, WhatIfDelta
from app.engine.cashflow import get_7day_projection, what_if_resolve
from app.models import ReconRun

router = APIRouter(prefix="/api/cashflow", tags=["cashflow"])
logger = logging.getLogger(__name__)


@router.get("/{run_id}", response_model=CashFlowResponse)
async def get_cashflow(run_id: str, db: Session = Depends(get_db)):
    """7-day cash-flow projection for a completed reconciliation run."""
    recon_run = db.query(ReconRun).filter(ReconRun.run_id == run_id).first()
    if not recon_run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    projection = get_7day_projection(db, run_id)

    total_confirmed = sum(d["confirmed_inflow"] for d in projection)
    total_disputed = sum(d["disputed_held"] for d in projection)

    return CashFlowResponse(
        run_id=run_id,
        projection=[CashFlowDayResponse(**d) for d in projection],
        total_confirmed=round(total_confirmed, 2),
        total_disputed=round(total_disputed, 2),
    )


@router.post("/whatif", response_model=WhatIfResponse)
async def resolve_break_whatif(request: WhatIfRequest, db: Session = Depends(get_db)):
    """Simulate resolving a break and return updated cash-flow projection."""
    result = what_if_resolve(db, request.run_id, request.break_order_id)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return WhatIfResponse(
        resolved_order_id=result["resolved_order_id"],
        base_projection=[CashFlowDayResponse(**d) for d in result["base_projection"]],
        whatif_projection=[CashFlowDayResponse(**d) for d in result["whatif_projection"]],
        deltas=[WhatIfDelta(**d) for d in result["deltas"]],
    )
