"""Тесты сравнения legacy vs NormalizedSignal."""
from decimal import Decimal

import pytest

from app.models.normalized_signal import NormalizedSignal
from app.models.signal import Signal, SignalDirection
from app.services.shadow_divergence import build_ab_report, compare_pair


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


def test_build_ab_report_buckets_and_readiness():
    from app.core.database import SessionLocal, engine
    from app.models.base import Base

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.query(NormalizedSignal).filter(NormalizedSignal.id.in_([2001, 2002, 2003])).delete(
            synchronize_session=False
        )
        db.query(Signal).filter(Signal.id.in_([1001, 1002])).delete(synchronize_session=False)
        db.commit()

        legacy_1 = _minimal_legacy(id=1001)
        legacy_2 = _minimal_legacy(id=1002, direction=SignalDirection.SHORT)
        norm_1 = _minimal_norm(
            id=2001,
            raw_event_id=3001,
            message_version_id=4001,
            extraction_id=5001,
            legacy_signal_id=1001,
        )
        norm_2 = _minimal_norm(
            id=2002,
            raw_event_id=3002,
            message_version_id=4002,
            extraction_id=5002,
            legacy_signal_id=1002,
            direction="LONG",
        )
        norm_missing = _minimal_norm(
            id=2003,
            raw_event_id=3003,
            message_version_id=4003,
            extraction_id=5003,
            legacy_signal_id=999999,
        )
        db.add_all([legacy_1, legacy_2, norm_1, norm_2, norm_missing])
        db.commit()

        report = build_ab_report(db, limit=10, min_sample_size=2)

        assert report["sample_size"] == 3
        assert report["legacy_count"] >= 2
        assert report["canonical_count"] >= 3
        assert report["linked_canonical_count"] >= 3
        assert report["buckets"]["strong_match"] >= 1
        assert report["buckets"]["partial_match"] >= 1
        assert report["buckets"]["missing_legacy"] >= 1
        assert report["readiness"] in {
            "ready_for_review",
            "needs_review",
            "blocked",
            "insufficient_sample",
        }
    finally:
        db.query(NormalizedSignal).filter(NormalizedSignal.id.in_([2001, 2002, 2003])).delete(
            synchronize_session=False
        )
        db.query(Signal).filter(Signal.id.in_([1001, 1002])).delete(synchronize_session=False)
        db.commit()
        db.close()
