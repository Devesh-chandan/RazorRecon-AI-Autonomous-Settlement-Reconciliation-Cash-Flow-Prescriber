"""Health check API route."""
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.schemas import HealthResponse
from app.cache import check_redis_connectivity
from app.llm.groq_client import check_groq_connectivity

router = APIRouter(prefix="/api", tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Check DB, Redis, and Groq connectivity."""

    # Database check
    try:
        db.execute(text("SELECT 1"))
        db_status = {"status": "ok"}
    except Exception as e:
        db_status = {"status": "error", "message": str(e)}

    # Redis check
    redis_status = check_redis_connectivity()

    # Groq check
    groq_status = check_groq_connectivity()

    overall = "ok" if db_status["status"] == "ok" else "degraded"

    return HealthResponse(
        status=overall,
        database=db_status,
        redis=redis_status,
        groq=groq_status,
        version="2.0.0",
    )
