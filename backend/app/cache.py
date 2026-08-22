"""Redis cache layer for reconciliation results."""
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is None:
        try:
            import redis
            from app.config import get_settings
            settings = get_settings()
            _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            _redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}. Caching disabled — falling back to DB reads.")
            _redis_client = None
    return _redis_client


def cache_results(run_id: str, data: Any, ttl: int = 300) -> bool:
    """Cache reconciliation results. Returns True on success."""
    client = _get_redis()
    if not client:
        return False
    try:
        key = f"razorrecon:results:{run_id}"
        client.setex(key, ttl, json.dumps(data, default=str))
        return True
    except Exception as e:
        logger.warning(f"Cache write failed for {run_id}: {e}")
        return False


def get_cached_results(run_id: str) -> Any | None:
    """Retrieve cached results. Returns None if cache miss or unavailable."""
    client = _get_redis()
    if not client:
        return None
    try:
        key = f"razorrecon:results:{run_id}"
        raw = client.get(key)
        return json.loads(raw) if raw else None
    except Exception as e:
        logger.warning(f"Cache read failed for {run_id}: {e}")
        return None


def invalidate(run_id: str) -> bool:
    """Invalidate cached results for a run (e.g., after what-if resolve)."""
    client = _get_redis()
    if not client:
        return False
    try:
        key = f"razorrecon:results:{run_id}"
        client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Cache invalidation failed for {run_id}: {e}")
        return False


def check_redis_connectivity() -> dict:
    """Health check for Redis."""
    client = _get_redis()
    if not client:
        return {"status": "unavailable", "message": "Redis not connected"}
    try:
        client.ping()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
