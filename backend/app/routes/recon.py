"""Reconciliation API routes — REST + SSE."""
import asyncio
import json
import uuid
import logging
from decimal import Decimal
from datetime import datetime, timezone
from typing import cast, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ReconRun, ReconResult
from app.schemas import ReconRunResponse, ReconResultResponse, ReconStatsResponse
from app.engine.reconcile import run_reconciliation, get_sse_queue, cleanup_sse_queue
from app.cache import get_cached_results

router = APIRouter(prefix="/api/recon", tags=["reconciliation"])
logger = logging.getLogger(__name__)


@router.post("/run", response_model=ReconRunResponse)
async def trigger_recon(
    background_tasks: BackgroundTasks,
    scope: str = "all",
    db: Session = Depends(get_db),
):
    """Trigger a new reconciliation run. Returns run_id immediately; progress via SSE.
    
    Query Params:
        scope: 'all' (audits all DB records) or 'imported' (audits imported/bulk records only).
    """
    run_id = str(uuid.uuid4())

    recon_run = ReconRun(run_id=run_id, status="running")
    db.add(recon_run)
    db.commit()

    # Run reconciliation in the background (async)
    from app.database import SessionLocal

    async def _run():
        bg_db = SessionLocal()
        try:
            if scope == "all":
                from app.seed import seed
                seed(seed_val=None)  # Generate fresh bounded random dataset
            await run_reconciliation(run_id, bg_db, scope=scope)
        except Exception as e:
            logger.error(f"Background recon failed: {e}", exc_info=True)
        finally:
            bg_db.close()

    background_tasks.add_task(_run)

    logger.info(f"Started reconciliation run: {run_id}")
    return ReconRunResponse(run_id=run_id, status="running")


@router.get("/stream/{run_id}")
async def stream_recon(run_id: str):
    """SSE endpoint — streams pass-by-pass progress events."""

    async def event_generator():
        queue = get_sse_queue(run_id)
        if queue is None:
            # Create a temporary queue and wait briefly for it to be populated
            await asyncio.sleep(0.1)
            queue = get_sse_queue(run_id)

        timeout_seconds = 120
        elapsed = 0

        while elapsed < timeout_seconds:
            if queue is None:
                queue = get_sse_queue(run_id)
                if queue is None:
                    await asyncio.sleep(0.2)
                    elapsed += 0.2
                    continue

            try:
                event_data = await asyncio.wait_for(queue.get(), timeout=1.0)
                yield {
                    "event": event_data["event"],
                    "data": json.dumps(event_data["data"]),
                }
                if event_data["event"] in ("complete", "error"):
                    cleanup_sse_queue(run_id)
                    break
            except asyncio.TimeoutError:
                # Send keepalive
                yield {"event": "keepalive", "data": json.dumps({"t": elapsed})}
                elapsed += 1

    return EventSourceResponse(event_generator())


@router.get("/results/{run_id}", response_model=list[ReconResultResponse])
async def get_results(run_id: str, db: Session = Depends(get_db)):
    """Full reconciliation results (all records)."""
    # Try Redis cache first — cached data is a list of plain dicts
    cached = get_cached_results(run_id)
    if cached:
        # Enrich cached dicts with required fields if missing
        enriched = []
        for i, item in enumerate(cached):
            enriched.append(ReconResultResponse(
                id=item.get("id", i + 1),
                run_id=item.get("run_id", run_id),
                order_id=item.get("order_id", ""),
                settlement_id=item.get("settlement_id"),
                ledger_id=item.get("ledger_id"),
                pass_number=item.get("pass_number", 1),
                status=item.get("status", "matched"),
                confidence=item.get("confidence"),
                flags=item.get("flags") or [],
                delta=item.get("delta") or {},
                root_cause=item.get("root_cause"),
                explanation_en=item.get("explanation_en"),
                explanation_hi=item.get("explanation_hi"),
                suggested_action=item.get("suggested_action"),
                severity=item.get("severity"),
                created_at=item.get("created_at"),
                amount=item.get("amount"),
                settlement_credit=item.get("settlement_credit"),
                # Gateway Performance Matrix fields
                gateway=item.get("gateway"),
                payment_method=item.get("payment_method"),
            ))
        return enriched

    # DB fallback — join Settlement & Order to get actual amounts and gateway metadata
    from app.models import Settlement, Order
    def parse_run_uuid(rid: str) -> uuid.UUID:
        try:
            return uuid.UUID(str(rid))
        except ValueError:
            return uuid.uuid5(uuid.NAMESPACE_DNS, str(rid))

    run_uuid = parse_run_uuid(run_id)
    results = db.query(ReconResult).filter(ReconResult.run_id == run_uuid).all()
    if not results:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found or still running")

    # Build settlement and order lookups keyed by order_id
    order_ids = [r.order_id for r in results]
    settlements = db.query(Settlement).filter(Settlement.order_id.in_(order_ids)).all()
    orders = db.query(Order).filter(Order.order_id.in_(order_ids)).all()
    settlement_by_order: dict[str, Settlement] = {s.order_id: s for s in settlements}
    order_by_id: dict[str, Order] = {o.order_id: o for o in orders}

    enriched_db = []
    for r in results:
        s = settlement_by_order.get(r.order_id)
        o = order_by_id.get(r.order_id)
        enriched_db.append(ReconResultResponse(
            id=r.id,
            run_id=str(r.run_id),
            order_id=r.order_id,
            settlement_id=r.settlement_id,
            ledger_id=r.ledger_id,
            pass_number=r.pass_number,
            status=r.status,
            confidence=float(r.confidence) if r.confidence is not None else None,
            flags=r.flags or [],
            delta=r.delta or {},
            root_cause=r.root_cause,
            explanation_en=r.explanation_en,
            explanation_hi=r.explanation_hi,
            suggested_action=r.suggested_action,
            severity=r.severity,
            created_at=r.created_at,
            amount=float(s.amount) if s and s.amount is not None else None,
            settlement_credit=float(s.credit) if s and s.credit is not None else None,
            # Gateway Performance Matrix fields
            gateway=str(s.gateway) if s and s.gateway else None,
            payment_method=str(o.method) if o and o.method else None,
        ))
    return enriched_db


@router.get("/stats/{run_id}", response_model=ReconStatsResponse)
async def get_stats(run_id: str, db: Session = Depends(get_db)):
    """Aggregated statistics for a reconciliation run."""
    recon_run = db.query(ReconRun).filter(ReconRun.run_id == run_id).first()
    if not recon_run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    _total: int = cast(int, recon_run.total_records) if recon_run.total_records is not None else 0
    _matched: int = cast(int, recon_run.matched_count) if recon_run.matched_count is not None else 0
    _breaks: int = cast(int, recon_run.break_count) if recon_run.break_count is not None else 0
    _rate: float = float(cast(Decimal, recon_run.match_rate)) if recon_run.match_rate is not None else 0.0
    _payout: float = float(cast(Decimal, recon_run.net_payout)) if recon_run.net_payout is not None else 0.0
    _status: str = cast(str, recon_run.status)

    return ReconStatsResponse(
        run_id=str(recon_run.run_id),
        total_records=_total,
        matched_count=_matched,
        break_count=_breaks,
        match_rate=_rate,
        net_payout=_payout,
        status=_status,
    )


@router.api_route("/cron", methods=["GET", "POST", "HEAD"], summary="Lightweight Cron Reconciliation Trigger")
async def trigger_cron_recon(
    background_tasks: BackgroundTasks,
    scope: str = "all",
    db: Session = Depends(get_db),
):
    """Cron-friendly reconciliation trigger returning lightweight HTTP 200 JSON (~75 bytes).
    
    Prevents hosting platform (e.g., cron-job.org, Render) HTTP response buffer overflow by
    returning a minimal JSON response while executing reconciliation asynchronously in the background.
    Supports both GET and POST HTTP methods used by various cron providers.
    """
    run_id = str(uuid.uuid4())
    recon_run = ReconRun(run_id=run_id, status="running")
    db.add(recon_run)
    db.commit()

    from app.database import SessionLocal

    async def _run():
        bg_db = SessionLocal()
        try:
            await run_reconciliation(run_id, bg_db, scope=scope)
        except Exception as e:
            logger.error(f"Cron background recon failed: {e}", exc_info=True)
        finally:
            bg_db.close()

    background_tasks.add_task(_run)
    logger.info(f"Cron scheduled reconciliation run started: {run_id}")
    return {"status": "ok", "message": "Reconciliation job started", "run_id": run_id}


