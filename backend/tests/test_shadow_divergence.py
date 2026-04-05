"""Тесты сравнения legacy vs NormalizedSignal."""
from decimal import Decimal

import pytest

from app.models.normalized_signal import NormalizedSignal
from app.models.signal import Signal, SignalDirection
from app.services.shadow_divergence import compare_pair


def _minimal_legacy(**kwargs):
    defaults = dict(
        channel_id=1,
        asset="BTC/USDT",
        symbol="BTC/USDT",
        direction=SignalDirection.LONG,
        entry_price=Decimal("50000.00"),
    )
    defaults.update(kwargs)
    return Signal(**defaults)


def _minimal_norm(**kwargs):
    defaults = dict(
        raw_event_id=1,
        message_version_id=1,
        extraction_id=1,
        legacy_signal_id=1,
        asset="BTCUSDT",
        direction="LONG",
        entry_price=Decimal("50000.00"),
    )
    defaults.update(kwargs)
    return NormalizedSignal(**defaults)


def test_compare_pair_perfect_match():
    leg = _minimal_legacy()
    norm = _minimal_norm()
    out = compare_pair(leg, norm)
    assert out["asset_match"] is True
    assert out["direction_match"] is True
    assert out["match_score"] >= 0.99


def test_compare_pair_direction_mismatch():
    leg = _minimal_legacy(direction=SignalDirection.SHORT)
    norm = _minimal_norm(direction="LONG")
    out = compare_pair(leg, norm)
    assert out["direction_match"] is False
    assert out["match_score"] < 0.9


def test_compare_pair_price_tolerance():
    leg = _minimal_legacy(entry_price=Decimal("100"))
    norm = _minimal_norm(entry_price=Decimal("100.05"))
    out = compare_pair(leg, norm)
    assert out["entry_price_relative_diff"] < 0.01


def test_compare_pair_large_price_diff_lowers_score():
    leg = _minimal_legacy(entry_price=Decimal("100"))
    norm = _minimal_norm(entry_price=Decimal("200"))
    out = compare_pair(leg, norm)
    # Цена даёт 0 в трети; asset+dir остаются совпадениями → ~0.67
    assert out["match_score"] < 0.75
    assert out["entry_price_relative_diff"] > 0.4
