"""FastAPI application factory — assembles routes, CORS, rate limiting, and lifespan."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy import text

from app.config import get_settings
from app.database import engine, SessionLocal, Base
import app.models  # noqa: F401
from app.routes import recon, cashflow, audit, health
from app.routes import auth as auth_routes
from app.routes import ingestion

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()

# ── Rate Limiter ───────────────────────────────────────────────────────────────
# Key = client IP address. Limit configured via RATE_LIMIT_PER_MINUTE env var.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup + shutdown."""
    # ── Startup ───────────────────────────────────────────────────────────────
    logger.info("🚀 RazorRecon & Flow API starting up...")

    # Verify DB connection & ensure tables exist
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("✅ Database connection & tables OK")
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

    # Warn if webhook secret is not configured
    if not settings.RAZORPAY_WEBHOOK_SECRET:
        logger.warning("⚠️  RAZORPAY_WEBHOOK_SECRET not set — webhook signatures will NOT be verified")

    # Warn if default JWT secret is in use
    if settings.JWT_SECRET_KEY == "change-me-in-production-use-openssl-rand-hex-32":
        logger.warning("⚠️  Using default JWT_SECRET_KEY — replace with `openssl rand -hex 32` in production")

    logger.info(f"🛡️  Rate limit: {settings.RATE_LIMIT_PER_MINUTE} req/min per IP")
    logger.info("✅ RazorRecon & Flow API ready")
    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("👋 RazorRecon & Flow API shutting down")


app = FastAPI(
    title="RazorRecon & Flow",
    description="LLM-Powered Settlement Reconciliation & Cash-Flow Prescriber",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Rate Limiting Middleware ───────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── CORS & Preflight Middleware ──────────────────────────────────────────────────
@app.middleware("http")
async def options_preflight_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        origin = request.headers.get("origin", "*")
        response = JSONResponse(content={"status": "ok"})
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response
    return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ─────────────────────────────────────────────────────────────────────
app.include_router(recon.router)
app.include_router(cashflow.router)
app.include_router(audit.router)
app.include_router(health.router)
app.include_router(auth_routes.router)
app.include_router(ingestion.router)


@app.get("/")
async def root():
    return {
        "app": "RazorRecon & Flow",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/health",
        "auth": "/api/auth/token",
        "webhook": "/api/webhooks/razorpay",
        "upload": "/api/recon/upload",
    }
