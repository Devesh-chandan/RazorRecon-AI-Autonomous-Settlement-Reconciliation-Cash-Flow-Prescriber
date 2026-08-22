"""
Pass 4 — LLM Exception Diagnostics via Groq / Llama 3.3 70B.

Analyzes genuine breaks that Passes 1-3 couldn't match,
generates bilingual (EN + Hinglish) explanations.
"""
import logging
from typing import Any

from app.llm.groq_client import analyze_breaks

logger = logging.getLogger(__name__)


def run_pass4(breaks: list[dict]) -> list[dict]:
    """
    Send all remaining breaks to Llama 3.3 via Groq for diagnosis.

    Args:
        breaks: list of break dicts from Pass 3
            { order_id, settlement, erp, order }

    Returns:
        list of enriched break dicts with LLM fields:
            { ...original, root_cause, explanation_en, explanation_hi,
              suggested_action, confidence, severity, pass_number=4, status="break" }
    """
    if not breaks:
        return []

    logger.info(f"Pass 4: sending {len(breaks)} breaks to LLM for analysis")

    diagnostics = analyze_breaks(breaks)

    results = []
    for i, (break_item, diag) in enumerate(zip(breaks, diagnostics)):
        result = {
            **break_item,
            "root_cause": diag.get("root_cause", "unknown"),
            "explanation_en": diag.get("explanation_en", ""),
            "explanation_hi": diag.get("explanation_hi", ""),
            "suggested_action": diag.get("suggested_action", ""),
            "confidence": diag.get("confidence", 0.5),
            "severity": diag.get("severity", "medium"),
            "flags": break_item.get("flags", []),
            "delta": break_item.get("delta", {}),
            "pass_number": 4,
            "status": "break",
        }
        results.append(result)
        logger.debug(
            f"  Break {i+1}/{len(breaks)}: {break_item['order_id']} → "
            f"{diag.get('root_cause')} [{diag.get('severity')}] conf={diag.get('confidence'):.2f}"
        )

    logger.info(f"Pass 4 complete: {len(results)} breaks diagnosed")
    return results
