"""FastAPI application factory — assembles routes, CORS, and lifespan."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import get_settings
from app.database import engine, SessionLocal
from app.routes import recon, cashflow, audit, health

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup + shutdown."""
    # ── Startup ───────────────────────────────────────────────────────────────
    logger.info("🚀 RazorRecon & Flow API starting up...")

    # Verify DB connection
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("✅ Database connection OK")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")

    # Verify Redis
    from app.cache import check_redis_connectivity
    redis_status = check_redis_connectivity()
    if redis_status["status"] == "ok":
        logger.info("✅ Redis connection OK")
    else:
        logger.warning(f"⚠️  Redis unavailable: {redis_status.get('message')} — falling back to DB reads")

    # Verify Groq
    if settings.GROQ_API_KEY:
        logger.info(f"✅ Groq API key configured (model: {settings.GROQ_MODEL})")
    else:
        logger.warning("⚠️  GROQ_API_KEY not set — LLM pass will use fallback diagnostics")

    logger.info("✅ RazorRecon & Flow API ready")
    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("👋 RazorRecon & Flow API shutting down")


app = FastAPI(
    title="RazorRecon & Flow",
    description="LLM-Powered Settlement Reconciliation & Cash-Flow Prescriber",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ─────────────────────────────────────────────────────────────────────
app.include_router(recon.router)
app.include_router(cashflow.router)
app.include_router(audit.router)
app.include_router(health.router)


@app.get("/")
async def root():
    return {
        "app": "RazorRecon & Flow",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }
