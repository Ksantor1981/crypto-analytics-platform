"""
G4 acceptance: execution models дают РАЗЛИЧИМЫЕ outcomes на одном и том же сценарии.

Без этого свойства SignalOutcome × ExecutionModel — фикция:
  scoring/A-B legacy↔canonical не сможет сравнить модели исполнения.

См. docs/TZ_APPENDIX_DATA_PLANE_ACCEPTANCE.md (G4) и docs/AUDIT_REPORT_2026_04_28.md.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.services.outcome_candle_engine import (
    OhlcCandle,
    compute_outcome_from_candles,
)


def _candle(ts_open: datetime, *, o: float, h: float, l: float, c: float) -> OhlcCandle:
    return OhlcCandle(
        ts_open=ts_open,
        open=Decimal(str(o)),
        high=Decimal(str(h)),
        low=Decimal(str(l)),
        close=Decimal(str(c)),
    )


def _scenario_long_tp_hits():
    """LONG, entry_zone=[100,110], entry_price=110, midpoint=105, TP=130, SL=90.

    Свеча 0 (signal_time): диапазон [108..125], close=115.
    Свеча 1: глубокий wick 104, TP-hit 132.
    Свеча 2: после TP.

    Ожидаемый эффект:
      market_on_publish  -> entry_fill = close(0) = 115
      first_touch_limit  -> entry_fill = 110 (касается уже на свече 0)
      midpoint_entry     -> entry_fill = 105 (касается только на свече 1, где low=104)
    Все три модели должны выдать COMPLETE+TP, но с разной entry_fill_price.
    """
    t0 = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)
    candles = [
        _candle(t0,                          o=120, h=125, l=108, c=115),
        _candle(t0 + timedelta(hours=1),     o=115, h=132, l=104, c=130),
        _candle(t0 + timedelta(hours=2),     o=130, h=135, l=128, c=132),
    ]
    return {
        "direction": "LONG",
        "entry_price": Decimal("110"),
        "midpoint_price": Decimal("105"),
        "take_profit": Decimal("130"),
        "stop_loss": Decimal("90"),
        "signal_time": t0,
        "candles": candles,
        "timeframe": "1h",
    }


def test_g4_three_models_produce_distinct_entry_fill_prices():
    s = _scenario_long_tp_hits()
    results = {}
    for model_key in ("market_on_publish", "first_touch_limit", "midpoint_entry"):
        status, fields = compute_outcome_from_candles(
            model_key=model_key,
            direction=s["direction"],
            entry_price=s["entry_price"],
            take_profit=s["take_profit"],
            stop_loss=s["stop_loss"],
            signal_time=s["signal_time"],
            candles=s["candles"],
            timeframe=s["timeframe"],
            midpoint_price=s["midpoint_price"],
            mop_reference="close",
        )
        assert status == "COMPLETE", f"{model_key}: ожидаем COMPLETE, получили {status} ({fields!r})"
        assert fields["entry_reached"] is True, f"{model_key}: entry_reached должно быть True"
        results[model_key] = fields

    fills = {k: v["entry_fill_price"] for k, v in results.items()}
    assert fills["market_on_publish"] == Decimal("115"), fills
    assert fills["first_touch_limit"] == Decimal("110"), fills
    assert fills["midpoint_entry"] == Decimal("105"), fills
    assert len(set(fills.values())) == 3, (
        f"G4 violation: модели должны различаться по entry_fill_price, получили {fills}"
    )


def test_g4_three_models_produce_distinct_mfe_mae():
    """MFE/MAE рассчитываются от entry_fill_price → должны различаться при равной свече."""
    s = _scenario_long_tp_hits()
    mfe_mae = {}
    for model_key in ("market_on_publish", "first_touch_limit", "midpoint_entry"):
        status, fields = compute_outcome_from_candles(
            model_key=model_key,
            direction=s["direction"],
            entry_price=s["entry_price"],
            take_profit=s["take_profit"],
            stop_loss=s["stop_loss"],
            signal_time=s["signal_time"],
            candles=s["candles"],
            timeframe=s["timeframe"],
            midpoint_price=s["midpoint_price"],
            mop_reference="close",
        )
        assert status == "COMPLETE"
        mfe_mae[model_key] = (fields["mfe"], fields["mae"])

    distinct_mfes = {v[0] for v in mfe_mae.values()}
    assert len(distinct_mfes) >= 2, f"MFE между моделями практически не различается: {mfe_mae}"


def test_g4_market_on_publish_does_not_use_limit_entry_price():
    """market_on_publish обязан игнорировать entry_price и брать reference со свечи публикации."""
    s = _scenario_long_tp_hits()
    status, fields = compute_outcome_from_candles(
        model_key="market_on_publish",
        direction=s["direction"],
        entry_price=Decimal("999999"),
        take_profit=s["take_profit"],
        stop_loss=s["stop_loss"],
        signal_time=s["signal_time"],
        candles=s["candles"],
        timeframe=s["timeframe"],
        mop_reference="close",
    )
    assert status == "COMPLETE"
    assert fields["entry_fill_price"] == Decimal("115"), fields


def test_g4_first_touch_limit_fails_if_entry_not_touched():
    """first_touch_limit должен отдать DATA_INCOMPLETE, если лимит не касался свечей."""
    t0 = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)
    candles = [_candle(t0, o=120, h=125, l=118, c=122)]
    status, fields = compute_outcome_from_candles(
        model_key="first_touch_limit",
        direction="LONG",
        entry_price=Decimal("110"),
        take_profit=Decimal("130"),
        stop_loss=Decimal("90"),
        signal_time=t0,
        candles=candles,
        timeframe="1h",
    )
    assert status == "DATA_INCOMPLETE"
    assert fields["entry_reached"] is False
    assert fields["error_detail"]["code"] == "entry_not_touched"


def test_g4_unknown_model_returns_error():
    t0 = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)
    candles = [_candle(t0, o=100, h=110, l=95, c=105)]
    status, fields = compute_outcome_from_candles(
        model_key="lunar_oracle_v0",
        direction="LONG",
        entry_price=Decimal("100"),
        take_profit=Decimal("120"),
        stop_loss=Decimal("90"),
        signal_time=t0,
        candles=candles,
        timeframe="1h",
    )
    assert status == "ERROR"
    assert fields["error_detail"]["code"] == "unknown_model_key"
