"""Reconciliation API routes — REST + SSE."""
import asyncio
import json
import uuid
import logging
from datetime import datetime, timezone

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
            ))
        return enriched

    results = db.query(ReconResult).filter(ReconResult.run_id == run_id).all()
    if not results:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found or still running")

    return [ReconResultResponse.model_validate(r) for r in results]


@router.get("/stats/{run_id}", response_model=ReconStatsResponse)
async def get_stats(run_id: str, db: Session = Depends(get_db)):
    """Aggregated statistics for a reconciliation run."""
    recon_run = db.query(ReconRun).filter(ReconRun.run_id == run_id).first()
    if not recon_run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    return ReconStatsResponse.model_validate(recon_run)


@router.post("/cron", status_code=204, summary="Lightweight Cron Reconciliation Trigger")
async def trigger_cron_recon(
    background_tasks: BackgroundTasks,
    scope: str = "all",
    db: Session = Depends(get_db),
):
    """Cron-friendly reconciliation trigger returning HTTP 204 No Content.
    
    Prevents hosting platform HTTP response buffer overflow by returning an empty body while
    executing reconciliation headlessly in the background.
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
    return Response(status_code=204)

