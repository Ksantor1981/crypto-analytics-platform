"""Тесты app.core.service_probes."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.service_probes import probe_ml_service, probe_redis_sync


@pytest.mark.asyncio
async def test_probe_ml_empty_url():
    ok, err = await probe_ml_service("")
    assert ok is False
    assert err and "empty" in err


@pytest.mark.asyncio
async def test_probe_ml_health_200():
    resp = MagicMock()
    resp.status_code = 200
    client = MagicMock()
    client.get = AsyncMock(return_value=resp)
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=client)
    cm.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=cm):
        ok, err = await probe_ml_service("http://ml:8000")
    assert ok is True
    assert err is None


@pytest.mark.asyncio
async def test_probe_ml_health_non_200():
    resp = MagicMock()
    resp.status_code = 503
    client = MagicMock()
    client.get = AsyncMock(return_value=resp)
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=client)
    cm.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=cm):
        ok, err = await probe_ml_service("http://ml:8000")
    assert ok is False
    assert err and "503" in err


@pytest.mark.asyncio
async def test_probe_ml_request_failure():
    client = MagicMock()
    client.get = AsyncMock(side_effect=RuntimeError("conn refused"))
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=client)
    cm.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=cm):
        ok, err = await probe_ml_service("http://ml:8000")
    assert ok is False
    assert err and "conn refused" in err


def test_probe_redis_empty_url():
    ok, err = probe_redis_sync("")
    assert ok is False and err and "empty" in err


def test_probe_redis_ping_ok():
    r = MagicMock()
    r.ping = MagicMock(return_value=True)
    with patch("redis.from_url", return_value=r):
        ok, err = probe_redis_sync("redis://localhost:6379/0")
    assert ok is True and err is None


def test_probe_redis_ping_false():
    r = MagicMock()
    r.ping = MagicMock(return_value=False)
    with patch("redis.from_url", return_value=r):
        ok, err = probe_redis_sync("redis://localhost:6379/0")
    assert ok is False and "ping" in (err or "").lower()


def test_probe_redis_from_url_error():
    with patch("redis.from_url", side_effect=OSError("nope")):
        ok, err = probe_redis_sync("redis://localhost:6379/0")
    assert ok is False
    assert "nope" in (err or "")
