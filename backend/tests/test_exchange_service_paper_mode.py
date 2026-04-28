"""F13/F-live регрессии для ExchangeService.

Проверяем, что default остаётся безопасным paper-mode, а live-mode строит
реальные подписанные HTTP-вызовы через мокнутый transport без внешних запросов.
"""
from __future__ import annotations

import asyncio
from decimal import Decimal

import pytest

from app.models.trading import ExchangeType
from app.services.exchange_service import ExchangeService


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def svc(monkeypatch):
    monkeypatch.setenv("EXCHANGE_PAPER_MODE", "true")
    monkeypatch.setenv("EXCHANGE_LIVE_TRADING_ENABLED", "false")
    return ExchangeService()


def test_default_is_paper_mode(svc):
    assert svc._is_paper_mode() is True


def test_place_order_returns_paper_marker(svc):
    res = _run(
        svc.place_order(
            ExchangeType.BYBIT,
            api_key="dummy",
            api_secret="dummy",
            passphrase=None,
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            quantity=Decimal("0.01"),
            price=None,
        )
    )
    assert res["mode"] == "paper"
    assert res["order_id"].startswith("paper_bybit_")
    assert res["status"] == "NEW"


def test_get_balance_returns_paper_marker(svc):
    res = _run(svc.get_account_balance(ExchangeType.BINANCE, "k", "s", None))
    assert res["mode"] == "paper"
    assert res["exchange"] == "binance"


@pytest.fixture
def live_svc(monkeypatch):
    monkeypatch.setenv("EXCHANGE_PAPER_MODE", "false")
    monkeypatch.setenv("EXCHANGE_LIVE_TRADING_ENABLED", "true")
    monkeypatch.setenv("EXCHANGE_BINANCE_BASE_URL", "https://binance.test")
    monkeypatch.setenv("EXCHANGE_BYBIT_BASE_URL", "https://bybit.test")
    return ExchangeService()


def test_live_binance_place_order_uses_signed_http_transport(live_svc, monkeypatch):
    calls = []

    async def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return {
            "orderId": 12345,
            "clientOrderId": "client-1",
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "LIMIT",
            "status": "NEW",
        }

    monkeypatch.setattr(live_svc, "_request_json", fake_request)

    res = _run(
        live_svc.place_order(
            ExchangeType.BINANCE,
            api_key="key",
            api_secret="secret",
            passphrase=None,
            symbol="BTCUSDT",
            side="BUY",
            order_type="LIMIT",
            quantity=Decimal("0.01"),
            price=Decimal("42000"),
        )
    )

    assert res["mode"] == "live"
    assert res["orderId"] == 12345
    method, url, kwargs = calls[0]
    assert method == "POST"
    assert url == "https://binance.test/api/v3/order"
    assert kwargs["headers"]["X-MBX-APIKEY"] == "key"
    assert kwargs["params"]["signature"]
    assert kwargs["params"]["timeInForce"] == "GTC"


def test_live_bybit_balance_uses_signed_http_transport(live_svc, monkeypatch):
    calls = []

    async def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return {
            "retCode": 0,
            "result": {
                "list": [
                    {
                        "coin": [
                            {
                                "coin": "USDT",
                                "walletBalance": "100.5",
                                "availableToWithdraw": "80.5",
                            }
                        ]
                    }
                ]
            },
        }

    monkeypatch.setattr(live_svc, "_request_json", fake_request)

    res = _run(live_svc.get_account_balance(ExchangeType.BYBIT, "key", "secret", None))

    assert res["mode"] == "live"
    assert res["currencies"]["USDT"]["total"] == 100.5
    method, url, kwargs = calls[0]
    assert method == "GET"
    assert url == "https://bybit.test/v5/account/wallet-balance"
    assert kwargs["params"] == {"accountType": "UNIFIED"}
    assert kwargs["headers"]["X-BAPI-API-KEY"] == "key"
    assert kwargs["headers"]["X-BAPI-SIGN"]
