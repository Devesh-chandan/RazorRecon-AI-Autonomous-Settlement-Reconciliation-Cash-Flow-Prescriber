"""Configuration management via Pydantic Settings."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Logging ────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    # ── LLM ────────────────────────────────────────────────────────────────
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"   # valid Groq model name (no prefix)
    GROQ_TEMPERATURE: float = 0.1

    # ── Database ─────────────────────────────────────────────────────────────
    # For production use: postgresql://user:pass@host:5432/db?sslmode=require
    DATABASE_URL: str = "postgresql://razorrecon:razorrecon@localhost:5432/razorrecon"

    # ── Redis ─────────────────────────────────────────────────────────────────
    # For production TLS use: rediss://:password@host:6380/0
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL: int = 300  # 5 minutes

    # ── Razorpay Webhook ──────────────────────────────────────────────────────
    # Found in Razorpay Dashboard → Settings → Webhooks → Secret
    RAZORPAY_WEBHOOK_SECRET: str = ""

    # ── JWT Authentication ────────────────────────────────────────────────────
    # Generate a strong secret: openssl rand -hex 32
    JWT_SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60   # requests/minute per IP

    # ── MDR rates by payment method (per RBI mandate) ─────────────────────────
    MDR_RATES: dict = {
        "upi": 0.0000,
        "card": 0.0200,
        "netbanking": 0.0175,
        "wallet": 0.0250,
    }

    # ── Reconciliation tolerances ─────────────────────────────────────────────
    MDR_FEE_TOLERANCE: float = 5.00      # ₹5 fee variance
    AMOUNT_TOLERANCE_PCT: float = 0.02   # ±2% amount mismatch
    GST_ROUNDING_TOLERANCE: float = 0.02 # ₹0.02 GST rounding
    SETTLEMENT_WINDOW_DAYS: int = 3      # T+1 to T+3 settlement window

    # ── CORS origins ─────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "https://localhost",           # production Nginx
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
