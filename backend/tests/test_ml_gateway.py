"""Тесты app.services.ml_gateway (circuit, retries, httpx)."""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx


@pytest.fixture(autouse=True)
def _reset_ml_circuit():
    from app.services import ml_gateway as mg

    asyncio.run(mg._on_success())
    yield
    asyncio.run(mg._on_success())


def _mock_client_cm(mock_response):
    client = MagicMock()
    client.get = AsyncMock(return_value=mock_response)
    client.post = AsyncMock(return_value=mock_response)
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=client)
    cm.__aexit__ = AsyncMock(return_value=None)
    return cm


def _settings(retries=2, th=5, secs=60):
    s = MagicMock()
    s.ML_HTTP_RETRIES = retries
    s.ML_CIRCUIT_FAILURE_THRESHOLD = th
    s.ML_CIRCUIT_OPEN_SECONDS = secs
    return s


@pytest.mark.asyncio
async def test_ml_http_request_200_resets_circuit():
    from app.services import ml_gateway as mg

    ok = MagicMock()
    ok.status_code = 200
    with patch("app.services.ml_gateway.get_settings", return_value=_settings()):
        with patch(
            "app.services.ml_gateway.httpx.AsyncClient",
            return_value=_mock_client_cm(ok),
        ):
            r = await mg.ml_http_request("GET", "http://ml/health")
            assert r.status_code == 200


@pytest.mark.asyncio
async def test_ml_http_request_404_not_server_error():
    from app.services import ml_gateway as mg

    resp = MagicMock()
    resp.status_code = 404
    with patch("app.services.ml_gateway.get_settings", return_value=_settings()):
        with patch(
            "app.services.ml_gateway.httpx.AsyncClient",
            return_value=_mock_client_cm(resp),
        ):
            r = await mg.ml_http_request("GET", "http://ml/x")
            assert r.status_code == 404
    st = mg.circuit_status()
    assert st["failures"] == 0


@pytest.mark.asyncio
async def test_ml_http_500_opens_circuit_when_threshold_one():
    from app.services import ml_gateway as mg

    bad = MagicMock()
    bad.status_code = 500
    settings = _settings(retries=0, th=1)
    with patch("app.services.ml_gateway.get_settings", return_value=settings):
        with patch(
            "app.services.ml_gateway.httpx.AsyncClient",
            return_value=_mock_client_cm(bad),
        ):
            r = await mg.ml_http_request("GET", "http://ml/fail")
            assert r.status_code == 500
    assert mg.circuit_status()["failures"] >= 1

    with patch("app.services.ml_gateway.get_settings", return_value=settings):
        with pytest.raises(mg.MLCircuitOpenError):
            await mg.ml_http_request("GET", "http://ml/any")


@pytest.mark.asyncio
async def test_ml_http_request_error_after_retries_raises():
    from app.services import ml_gateway as mg

    client = MagicMock()
    client.get = AsyncMock(
        side_effect=httpx.RequestError("boom", request=MagicMock())
    )
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=client)
    cm.__aexit__ = AsyncMock(return_value=None)

    with patch("app.services.ml_gateway.get_settings", return_value=_settings(retries=0, th=99)):
        with patch("app.services.ml_gateway.httpx.AsyncClient", return_value=cm):
            with pytest.raises(httpx.RequestError):
                await mg.ml_http_request("GET", "http://ml/x")


@pytest.mark.asyncio
async def test_ml_http_retries_then_success():
    from app.services import ml_gateway as mg

    fail = MagicMock()
    fail.status_code = 503
    ok = MagicMock()
    ok.status_code = 200
    client = MagicMock()
    client.get = AsyncMock(side_effect=[fail, fail, ok])
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=client)
    cm.__aexit__ = AsyncMock(return_value=None)

    with patch("app.services.ml_gateway.get_settings", return_value=_settings(retries=2, th=5)):
        with patch("app.services.ml_gateway.asyncio.sleep", new_callable=AsyncMock):
            with patch("app.services.ml_gateway.httpx.AsyncClient", return_value=cm):
                r = await mg.ml_http_request("GET", "http://ml/")
                assert r.status_code == 200


def test_circuit_status_shape():
    from app.services import ml_gateway as mg

    st = mg.circuit_status()
    assert set(st.keys()) == {"failures", "open_until_monotonic", "blocked"}
    assert isinstance(st["blocked"], bool)


@pytest.mark.asyncio
async def test_ml_http_transient_request_error_then_success():
    from app.services import ml_gateway as mg

    ok = MagicMock()
    ok.status_code = 200
    err = httpx.RequestError("timeout", request=MagicMock())
    client = MagicMock()
    client.get = AsyncMock(side_effect=[err, ok])
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=client)
    cm.__aexit__ = AsyncMock(return_value=None)

    with patch("app.services.ml_gateway.get_settings", return_value=_settings(retries=1, th=5)):
        with patch("app.services.ml_gateway.asyncio.sleep", new_callable=AsyncMock):
            with patch("app.services.ml_gateway.httpx.AsyncClient", return_value=cm):
                r = await mg.ml_http_request("GET", "http://ml/retry")
                assert r.status_code == 200
