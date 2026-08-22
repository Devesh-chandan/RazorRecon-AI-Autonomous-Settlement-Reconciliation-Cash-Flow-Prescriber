"""
Groq Cloud API client for LLM-powered reconciliation diagnostics.

Uses Llama 3.3 70B Versatile via Groq Cloud (free tier, ~500 tok/s).
Falls back gracefully if API key is missing or rate-limited.
"""
import json
import logging
import time
from typing import Any

from app.config import get_settings
from app.llm.prompts import SYSTEM_PROMPT, BATCH_PROMPT_TEMPLATE, SINGLE_BREAK_TEMPLATE

logger = logging.getLogger(__name__)
settings = get_settings()

_groq_client = None


def _get_client():
    global _groq_client
    if _groq_client is None and settings.GROQ_API_KEY:
        try:
            from groq import Groq
            _groq_client = Groq(api_key=settings.GROQ_API_KEY)
        except ImportError:
            logger.warning("groq package not installed — LLM diagnostics disabled")
    return _groq_client


def _build_break_context(break_item: dict, index: int) -> str:
    """Serialize one break record into a readable prompt segment."""
    def _safe_serialize(obj):
        if obj is None:
            return "N/A"
        result = {}
        for k, v in obj.items():
            if hasattr(v, "isoformat"):
                result[k] = v.isoformat()
            else:
                try:
                    result[k] = float(v) if hasattr(v, "__float__") else str(v)
                except Exception:
                    result[k] = str(v)
        return result

    return SINGLE_BREAK_TEMPLATE.format(
        index=index + 1,
        order_id=break_item.get("order_id", "unknown"),
        settlement=json.dumps(_safe_serialize(break_item.get("settlement") or {}), indent=2),
        erp=json.dumps(_safe_serialize(break_item.get("erp") or {}), indent=2),
        order=json.dumps(_safe_serialize(break_item.get("order") or {}), indent=2),
    )


def _fallback_diagnostic(break_item: dict) -> dict:
    """Template diagnostic when Groq is unavailable."""
    order_id = break_item.get("order_id", "unknown")
    settlement = break_item.get("settlement") or {}
    order = break_item.get("order") or {}

    # Heuristic fallback
    if settlement.get("type") == "adjustment":
        root = "chargeback"
        sev = "high"
        en = f"This payment was reversed as a chargeback adjustment. The debit of ₹{settlement.get('debit', 0)} requires investigation and may need to be accepted as a loss."
        hi = f"Yeh payment chargeback ki wajah se reverse ho gaya hai. ₹{settlement.get('debit', 0)} ka debit investigate karna padega."
        action = "Review chargeback reason code with acquiring bank and decide whether to dispute or accept."
    elif not break_item.get("erp"):
        root = "missing_erp_entry"
        sev = "high"
        en = f"No ERP ledger entry found for order {order_id}. The settlement of ₹{settlement.get('amount', 0)} was received but not recorded in the internal system."
        hi = f"Order {order_id} ke liye ERP mein koi entry nahi mili. ₹{settlement.get('amount', 0)} ka settlement receive hua hai lekin record nahi hai."
        action = "Create a manual ERP ledger entry and reconcile with the settlement record."
    elif order.get("status") == "partial_refund":
        root = "partial_refund"
        sev = "medium"
        en = f"This order had a partial refund of ₹{order.get('refund_amount', 0)}. The net settlement credit does not match the ERP expected amount."
        hi = f"Is order mein ₹{order.get('refund_amount', 0)} ka partial refund tha. Net settlement credit ERP se match nahi kar raha."
        action = "Update ERP ledger to reflect the net amount after partial refund deduction."
    else:
        root = "unknown"
        sev = "medium"
        en = f"Unable to automatically classify this break for order {order_id}. Manual review is required to determine the root cause."
        hi = f"Order {order_id} ka break automatically classify nahi ho saka. Manual review zaroori hai."
        action = "Escalate to the finance team for manual investigation and ERP correction."

    return {
        "root_cause": root,
        "explanation_en": en,
        "explanation_hi": hi,
        "suggested_action": action,
        "confidence": 0.60,
        "severity": sev,
    }


def analyze_breaks(breaks: list[dict]) -> list[dict]:
    """
    Analyze a list of unreconciled breaks via Groq LLM.
    
    Returns a list of diagnostic dicts in the same order as input.
    Falls back gracefully on any error.
    """
    if not breaks:
        return []

    client = _get_client()
    if not client:
        logger.warning("Groq client unavailable — using fallback diagnostics for all breaks")
        return [_fallback_diagnostic(b) for b in breaks]

    # Build batch prompt
    breaks_context = "\n\n---\n\n".join(
        _build_break_context(b, i) for i, b in enumerate(breaks)
    )
    user_prompt = BATCH_PROMPT_TEMPLATE.format(
        count=len(breaks),
        breaks_json=breaks_context,
    )

    retries = 3
    backoff = 2.0

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                temperature=settings.GROQ_TEMPERATURE,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=4000,
            )

            raw = response.choices[0].message.content
            parsed = json.loads(raw)
            results = parsed.get("results", [])

            if len(results) != len(breaks):
                logger.warning(
                    f"LLM returned {len(results)} results for {len(breaks)} breaks — padding with fallbacks"
                )
                while len(results) < len(breaks):
                    results.append(_fallback_diagnostic(breaks[len(results)]))

            # Validate + sanitize each result
            valid_roots = {
                "mdr_variance", "timing_lag", "missing_erp_entry", "data_entry_error",
                "chargeback", "partial_refund", "gst_rounding", "duplicate_entry", "unknown"
            }
            valid_severities = {"low", "medium", "high", "critical"}

            for i, res in enumerate(results):
                if res.get("root_cause") not in valid_roots:
                    res["root_cause"] = "unknown"
                if res.get("severity") not in valid_severities:
                    res["severity"] = "medium"
                try:
                    res["confidence"] = float(res.get("confidence", 0.7))
                    res["confidence"] = max(0.0, min(1.0, res["confidence"]))
                except (ValueError, TypeError):
                    res["confidence"] = 0.70

            return results

        except Exception as e:
            logger.error(f"Groq API attempt {attempt + 1}/{retries} failed: {e}")
            if attempt < retries - 1:
                time.sleep(backoff * (2 ** attempt))
            else:
                logger.warning("All Groq retries exhausted — using fallback diagnostics")
                return [_fallback_diagnostic(b) for b in breaks]

    return [_fallback_diagnostic(b) for b in breaks]


def check_groq_connectivity() -> dict:
    """Health check for Groq connectivity."""
    if not settings.GROQ_API_KEY:
        return {"status": "no_key", "message": "GROQ_API_KEY not configured"}

    client = _get_client()
    if not client:
        return {"status": "error", "message": "Failed to initialize Groq client"}

    try:
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
        )
        return {"status": "ok", "model": settings.GROQ_MODEL}
    except Exception as e:
        return {"status": "error", "message": str(e)}
