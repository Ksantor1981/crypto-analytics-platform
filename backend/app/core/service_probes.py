"""Проверки доступности внешних сервисов (ML, Redis) для /health и корня API."""
from __future__ import annotations

import logging
from typing import Tuple

logger = logging.getLogger(__name__)


async def probe_ml_service(ml_url: str, timeout: float = 2.5) -> Tuple[bool, str | None]:
    """GET {ml_url}/health — возвращает (ok, error_message)."""
    base = (ml_url or "").rstrip("/")
    if not base:
        return False, "ML_SERVICE_URL empty"
    try:
        import httpx

        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(f"{base}/health")
            if r.status_code == 200:
                return True, None
            return False, f"HTTP {r.status_code}"
    except Exception as e:
        logger.debug("ML probe failed: %s", e)
        return False, str(e)


def probe_redis_sync(redis_url: str, timeout: float = 2.0) -> Tuple[bool, str | None]:
    """Синхронный ping Redis (для /health без async redis)."""
    if not redis_url:
        return False, "REDIS_URL empty"
    try:
        import redis

        r = redis.from_url(redis_url, socket_connect_timeout=timeout, socket_timeout=timeout)
        if r.ping():
            return True, None
        return False, "ping failed"
    except Exception as e:
        logger.debug("Redis probe failed: %s", e)
        return False, str(e)
