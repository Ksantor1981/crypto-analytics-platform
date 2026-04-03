"""
HTTP к ML-сервису: повторы при временных сбоях + circuit breaker (защита от каскада).
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_lock = asyncio.Lock()
_failures = 0
_open_until: float = 0.0


class MLCircuitOpenError(Exception):
    """Circuit открыт после серии ошибок ML-сервиса."""


async def _should_block() -> bool:
    return time.monotonic() < _open_until


async def _on_success() -> None:
    global _failures, _open_until
    async with _lock:
        _failures = 0
        _open_until = 0.0


async def _on_failure() -> None:
    global _failures, _open_until
    async with _lock:
        s = get_settings()
        th = max(1, int(getattr(s, "ML_CIRCUIT_FAILURE_THRESHOLD", 5)))
        secs = max(5, int(getattr(s, "ML_CIRCUIT_OPEN_SECONDS", 60)))
        _failures += 1
        if _failures >= th:
            _open_until = time.monotonic() + float(secs)
            logger.warning(
                "ML circuit OPEN %ss after %s consecutive failures",
                secs,
                _failures,
            )


def circuit_status() -> dict[str, Any]:
    """Для /health или отладки."""
    return {
        "failures": _failures,
        "open_until_monotonic": _open_until,
        "blocked": time.monotonic() < _open_until,
    }


async def ml_http_request(
    method: str,
    url: str,
    *,
    timeout: float = 30.0,
    **kwargs: Any,
) -> httpx.Response:
    """
    GET/POST к ML с короткими повторами и учётом circuit.
    5xx увеличивают счётчик после исчерпания повторов; 2xx/3xx/4xx сбрасывают счётчик.
    """
    if await _should_block():
        raise MLCircuitOpenError("ML service circuit is open")

    s = get_settings()
    retries = max(0, int(getattr(s, "ML_HTTP_RETRIES", 2)))
    last_err: Optional[Exception] = None

    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                fn = getattr(client, method.lower())
                r = await fn(url, **kwargs)
            if r.status_code < 500:
                await _on_success()
                return r
            last_err = None
            if attempt < retries:
                await asyncio.sleep(0.4 * (2**attempt))
                continue
            await _on_failure()
            return r
        except httpx.RequestError as e:
            last_err = e
            if attempt < retries:
                await asyncio.sleep(0.4 * (2**attempt))
                continue
            await _on_failure()
            raise

    if last_err:
        raise last_err
    raise RuntimeError("ml_http_request: unexpected end")
