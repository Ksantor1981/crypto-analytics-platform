"""
Redis cache layer for prices, channels, analytics.
TTL-based caching with fallback when Redis unavailable.
"""
import os
import json
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

_redis_client = None
_REDIS_DISABLED = False

CACHE_TTL_PRICE = 300      # 5 min
CACHE_TTL_CHANNELS = 60     # 1 min
CACHE_TTL_ANALYTICS = 120   # 2 min


def _get_redis():
    global _redis_client, _REDIS_DISABLED
    if _REDIS_DISABLED:
        return None
    if _redis_client is not None:
        return _redis_client
    try:
        import redis
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis_client = redis.from_url(url, decode_responses=True)
        _redis_client.ping()
        logger.info("Redis cache connected")
        return _redis_client
    except Exception as e:
        logger.warning(f"Redis cache unavailable: {e}")
        _REDIS_DISABLED = True
        return None


def cache_get(key: str) -> Optional[Any]:
    """Get value from Redis cache. Returns None if miss or Redis down."""
    r = _get_redis()
    if not r:
        return None
    try:
        data = r.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        logger.debug(f"Cache get failed for {key}: {e}")
    return None


def cache_set(key: str, value: Any, ttl: int = 300) -> bool:
    """Set value in Redis cache. Returns False if Redis down."""
    r = _get_redis()
    if not r:
        return False
    try:
        r.setex(key, ttl, json.dumps(value, default=str))
        return True
    except Exception as e:
        logger.debug(f"Cache set failed for {key}: {e}")
    return False


def cache_delete(key: str) -> bool:
    """Delete key from cache."""
    r = _get_redis()
    if not r:
        return False
    try:
        r.delete(key)
        return True
    except Exception:
        return False


# Key builders
def key_price(symbol: str) -> str:
    return f"price:{symbol.upper()}"


def key_channels_list(sort: str, skip: int, limit: int) -> str:
    return f"channels:list:{sort}:{skip}:{limit}"


def key_dashboard_signals(skip: int, limit: int) -> str:
    return f"dashboard:signals:{skip}:{limit}"


def key_dashboard_channels(skip: int, limit: int) -> str:
    return f"dashboard:channels:{skip}:{limit}"
