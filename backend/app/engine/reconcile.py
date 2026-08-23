"""
Reconciliation orchestrator — runs all 4 passes sequentially,
publishes SSE progress events, persists results.
"""
import asyncio
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import AsyncGenerator, Any

from sqlalchemy.orm import Session

from app.models import Order, Settlement, ErpLedger, ReconRun, ReconResult
from app.engine.pass1_exact import run_pass1
from app.engine.pass2_rules import run_pass2
from app.engine.pass3_fuzzy import run_pass3
from app.engine.pass4_llm import run_pass4
from app.cache import cache_results

logger = logging.getLogger(__name__)

# ── In-memory event queues for SSE streaming ──────────────────────────────────
_sse_queues: dict[str, asyncio.Queue] = {}


def _get_or_create_queue(run_id: str) -> asyncio.Queue:
    if run_id not in _sse_queues:
        _sse_queues[run_id] = asyncio.Queue()
    return _sse_queues[run_id]


def get_sse_queue(run_id: str) -> asyncio.Queue | None:
    return _sse_queues.get(run_id)


def cleanup_sse_queue(run_id: str):
    _sse_queues.pop(run_id, None)


def _model_to_dict(obj) -> dict:
    """Convert a SQLAlchemy model instance to a plain dict."""
    d = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, Decimal):
            val = float(val)
        elif hasattr(val, "isoformat"):
            val = val.isoformat()
        elif hasattr(val, "hex"):  # UUID
            val = str(val)
        d[col.name] = val
    return d


async def run_reconciliation(run_id: str, db: Session, scope: str = "all") -> None:
    """
    Full 4-pass reconciliation pipeline.
    Posts SSE events to the run_id queue as passes complete.
    
    Args:
        run_id: Unique UUID string for this run.
        db: SQLAlchemy DB session.
        scope: "all" (audits all DB records) or "imported" (audits only CSV/bulk imported records).
    """
    queue = _get_or_create_queue(run_id)
    start_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

    def elapsed() -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000) - start_ms

    async def emit(event_type: str, data: dict):
        await queue.put({"event": event_type, "data": data})

    try:
        # ── Load data from DB (scoped by parameter) ────────────────────────────
        orders_raw = db.query(Order).all()
        erp_raw = db.query(ErpLedger).all()

        if scope == "imported":
            from sqlalchemy import or_
            settlements_raw = db.query(Settlement).filter(
                or_(
                    Settlement.settlement_id.ilike("%csv%"),
                    Settlement.settlement_id.ilike("%bulk%"),
                    Settlement.order_id.ilike("%csv%"),
                    Settlement.order_id.ilike("%bulk%"),
                )
            ).all()
            if not settlements_raw:
                # Fallback to all if no specific csv/bulk prefix found
                settlements_raw = db.query(Settlement).all()
        else:
            settlements_raw = db.query(Settlement).all()

        orders = [_model_to_dict(o) for o in orders_raw]
        settlements = [_model_to_dict(s) for s in settlements_raw]
        erp_entries = [_model_to_dict(e) for e in erp_raw]

        total = len(settlements)

        await emit("progress", {
            "run_id": run_id,
            "pass": 0,
            "pass_name": "Loading Data",
            "matched_this_pass": 0,
            "total_matched": 0,
            "total_records": total,
            "elapsed_ms": elapsed(),
        })

        # ── Pass 1: Exact Match ────────────────────────────────────────────────
        await asyncio.sleep(0.2)  # brief delay for visual feedback
        p1 = run_pass1(settlements, erp_entries, orders)
        matched_count = len(p1["matched"])

        await emit("progress", {
            "run_id": run_id,
            "pass": 1,
            "pass_name": "Exact Deterministic Match",
            "matched_this_pass": len(p1["matched"]),
            "total_matched": matched_count,
            "total_records": total,
            "elapsed_ms": elapsed(),
        })
        logger.info(f"[{run_id}] Pass 1: {len(p1['matched'])} matched")

        # ── Pass 2: Rule-Based ─────────────────────────────────────────────────
        await asyncio.sleep(0.3)
        p2 = run_pass2(p1["unmatched_settlements"], p1["unmatched_erp"], p1["unmatched_orders"])
        matched_count += len(p2["matched"])

        await emit("progress", {
            "run_id": run_id,
            "pass": 2,
            "pass_name": "Rule-Based Contextual Match",
            "matched_this_pass": len(p2["matched"]),
            "total_matched": matched_count,
            "total_records": total,
            "elapsed_ms": elapsed(),
        })
        logger.info(f"[{run_id}] Pass 2: {len(p2['matched'])} matched")

        # ── Pass 3: Fuzzy Heuristic ────────────────────────────────────────────
        await asyncio.sleep(0.3)
        p3 = run_pass3(p2["unmatched_settlements"], p2["unmatched_erp"], p2["unmatched_orders"])
        matched_count += len(p3["matched"])

        await emit("progress", {
            "run_id": run_id,
            "pass": 3,
            "pass_name": "Fuzzy Heuristic Match",
            "matched_this_pass": len(p3["matched"]),
            "total_matched": matched_count,
            "total_records": total,
            "elapsed_ms": elapsed(),
        })
        logger.info(f"[{run_id}] Pass 3: {len(p3['matched'])} matched, {len(p3['breaks'])} breaks")

        # ── Pass 4: LLM Diagnostics ────────────────────────────────────────────
        await asyncio.sleep(0.2)
        await emit("progress", {
            "run_id": run_id,
            "pass": 4,
            "pass_name": "AI Exception Diagnostics (Llama 3.3 70B)",
            "matched_this_pass": 0,
            "total_matched": matched_count,
            "total_records": total,
            "elapsed_ms": elapsed(),
            "llm_analyzing": len(p3["breaks"]),
        })

        # Run LLM in thread pool to avoid blocking event loop
        loop = asyncio.get_running_loop()
        p4_results = await loop.run_in_executor(None, run_pass4, p3["breaks"])
        break_count = len(p4_results)

        logger.info(f"[{run_id}] Pass 4: {break_count} breaks diagnosed by LLM")

        # ── Persist results ────────────────────────────────────────────────────
        all_matched = [
            *[{**m, "status": "matched"} for m in p1["matched"]],
            *[{**m, "status": "matched"} for m in p2["matched"]],
            *[{**m, "status": "matched"} for m in p3["matched"]],
        ]

        recon_results_to_insert = []

        for match in all_matched:
            settlement = match.get("settlement") or {}
            erp = match.get("erp") or {}
            recon_results_to_insert.append(ReconResult(
                run_id=uuid.UUID(run_id),
                order_id=match["order_id"],
                settlement_id=settlement.get("settlement_id"),
                ledger_id=erp.get("ledger_id"),
                pass_number=match["pass_number"],
                status="matched",
                confidence=match.get("confidence", 1.0),
                flags=match.get("flags", []),
                delta=match.get("delta", {}),
                root_cause=None,
                explanation_en=None,
                explanation_hi=None,
                suggested_action=None,
                severity="low",
            ))

        for brk in p4_results:
            settlement = brk.get("settlement") or {}
            erp = brk.get("erp") or {}
            recon_results_to_insert.append(ReconResult(
                run_id=uuid.UUID(run_id),
                order_id=brk["order_id"],
                settlement_id=settlement.get("settlement_id"),
                ledger_id=erp.get("ledger_id") if erp else None,
                pass_number=4,
                status="break",
                confidence=brk.get("confidence", 0.5),
                flags=brk.get("flags", []),
                delta=brk.get("delta", {}),
                root_cause=brk.get("root_cause"),
                explanation_en=brk.get("explanation_en"),
                explanation_hi=brk.get("explanation_hi"),
                suggested_action=brk.get("suggested_action"),
                severity=brk.get("severity", "medium"),
            ))

        db.add_all(recon_results_to_insert)

        # Compute stats
        net_payout = sum(
            float(s.get("credit", 0))
            for m in all_matched
            if (s := m.get("settlement") or {}) and float(s.get("credit", 0)) > 0
        )
        match_rate = round((matched_count / total) * 100, 2) if total > 0 else 0.0

        # Update ReconRun record
        recon_run = db.query(ReconRun).filter(ReconRun.run_id == run_id).first()
        if recon_run:
            recon_run.status = "complete"
            recon_run.total_records = total
            recon_run.matched_count = matched_count
            recon_run.break_count = break_count
            recon_run.match_rate = match_rate
            recon_run.net_payout = net_payout
            recon_run.completed_at = datetime.now(timezone.utc)

        db.commit()

        # Cache results in Redis
        all_results_for_cache = []
        for r in recon_results_to_insert:
            all_results_for_cache.append({
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
            })

        await loop.run_in_executor(None, cache_results, run_id, all_results_for_cache)

        await emit("complete", {
            "run_id": run_id,
            "match_rate": match_rate,
            "matched": matched_count,
            "breaks": break_count,
            "net_payout": net_payout,
            "total_records": total,
            "elapsed_ms": elapsed(),
        })

    except Exception as e:
        logger.error(f"[{run_id}] Reconciliation failed: {e}", exc_info=True)
        # Update run status to error
        try:
            recon_run = db.query(ReconRun).filter(ReconRun.run_id == run_id).first()
            if recon_run:
                recon_run.status = "error"
                db.commit()
        except Exception:
            pass
        await emit("error", {
            "run_id": run_id,
            "message": str(e),
            "fallback": False,
        })
