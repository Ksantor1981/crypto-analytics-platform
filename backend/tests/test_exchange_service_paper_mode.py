"""F13 регресс: ExchangeService по умолчанию paper-mode и fail-loud в live-mode.

Проверяем, что MVP-поведение биржевого слоя честно помечено `mode: "paper"`
и не вводит в заблуждение оператора. См. docs/SYSTEM_AUDIT_2026_04_28.md F13.
"""
from __future__ import annotations

import asyncio
from decimal import Decimal

import pytest

from app.models.trading import ExchangeType
from app.services.exchange_service import ExchangeService


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


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


def test_live_mode_without_real_impl_fails_loud(monkeypatch):
    """EXCHANGE_LIVE_TRADING_ENABLED=true + paper=false → NotImplementedError."""
    monkeypatch.setenv("EXCHANGE_PAPER_MODE", "false")
    monkeypatch.setenv("EXCHANGE_LIVE_TRADING_ENABLED", "true")
    svc = ExchangeService()

    with pytest.raises(NotImplementedError):
        svc._ensure_paper_or_fail_loud("test")
