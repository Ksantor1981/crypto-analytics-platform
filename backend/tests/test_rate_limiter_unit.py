"""Юнит-тесты rate limiter (ТЗ: защита API)."""
import pytest
from unittest.mock import MagicMock

from fastapi import HTTPException
from slowapi.errors import RateLimitExceeded

from app.core.rate_limiter import (
    get_auth_rate_limit,
    get_general_rate_limit,
    rate_limit_exceeded_handler,
)


def test_get_auth_rate_limit_contains_window():
    s = get_auth_rate_limit()
    assert "second" in s
    assert "/" in s


def test_get_general_rate_limit_contains_window():
    s = get_general_rate_limit()
    assert "second" in s


@pytest.mark.asyncio
async def test_rate_limit_exceeded_handler_raises_429():
    request = MagicMock()
    request.url.path = "/api/v1/test"
    request.method = "GET"

    exc = MagicMock(spec=RateLimitExceeded)
    exc.detail = "10 per minute"
    type(exc).retry_after = 60

    with pytest.raises(HTTPException) as ctx:
        await rate_limit_exceeded_handler(request, exc)

    assert ctx.value.status_code == 429
    body = ctx.value.detail
    assert isinstance(body, dict)
    assert body.get("error") == "Rate limit exceeded"
