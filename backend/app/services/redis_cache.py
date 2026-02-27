"""Redis cache for frequently accessed data."""
import json
import logging
from typing import Optional
import redis

logger = logging.getLogger(__name__)

_client: Optional[redis.Redis] = None


def get_redis() -> Optional[redis.Redis]:
    global _client
    if _client is None:
        try:
            _client = redis.Redis(host='localhost', port=6379, db=0, socket_connect_timeout=2)
            _client.ping()
        except Exception:
            _client = None
    return _client


def cache_get(key: str) -> Optional[dict]:
    r = get_redis()
    if not r:
        return None
    try:
        data = r.get(f"crypto:{key}")
        return json.loads(data) if data else None
    except Exception:
        return None


def cache_set(key: str, value: dict, ttl: int = 300):
    r = get_redis()
    if not r:
        return
    try:
        r.setex(f"crypto:{key}", ttl, json.dumps(value))
    except Exception:
        pass


def cache_delete(key: str):
    r = get_redis()
    if not r:
        return
    try:
        r.delete(f"crypto:{key}")
    except Exception:
        pass
