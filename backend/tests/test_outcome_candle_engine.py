"""Юнит-тесты движка расчёта outcome по OHLC (без сети)."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.services.outcome_candle_engine import OhlcCandle, compute_outcome_from_candles, mop_reference_price


def test_market_on_publish_long_tp_hit():
    st = datetime(2025, 6, 1, 10, 30, tzinfo=timezone.utc)
    h = timedelta(hours=1)
    candles = [
        OhlcCandle(st.replace(minute=0), Decimal("100"), Decimal("105"), Decimal("99"), Decimal("101")),
        OhlcCandle(st.replace(minute=0) + h, Decimal("101"), Decimal("130"), Decimal("100"), Decimal("125")),
    ]
    status, fields = compute_outcome_from_candles(
        model_key="market_on_publish",
        direction="LONG",
        entry_price=Decimal("100"),
        take_profit=Decimal("110"),
        stop_loss=Decimal("90"),
        signal_time=st,
        candles=candles,
        timeframe="1h",
    )
    assert status == "COMPLETE"
    assert fields["entry_fill_price"] == Decimal("101")
    assert fields["sl_hit"] is False
    assert fields["tp_hits"]
    assert fields["expiry_hit"] is False


def test_market_on_publish_long_sl_before_tp_same_bar():
    st = datetime(2025, 6, 1, 10, 0, tzinfo=timezone.utc)
    h = timedelta(hours=1)
    candles = [
        OhlcCandle(st, Decimal("100"), Decimal("105"), Decimal("99"), Decimal("102")),
        OhlcCandle(st + h, Decimal("102"), Decimal("108"), Decimal("88"), Decimal("90")),
    ]
    status, fields = compute_outcome_from_candles(
        model_key="market_on_publish",
        direction="LONG",
        entry_price=Decimal("100"),
        take_profit=Decimal("120"),
        stop_loss=Decimal("95"),
        signal_time=st,
        candles=candles,
        timeframe="1h",
        sl_before_tp_same_bar=True,
    )
    assert status == "COMPLETE"
    assert fields["sl_hit"] is True
    assert not fields.get("tp_hits")


def test_market_on_publish_uses_mop_open():
    st = datetime(2025, 6, 1, 10, 30, tzinfo=timezone.utc)
    h = timedelta(hours=1)
    c0 = OhlcCandle(st.replace(minute=0), Decimal("50"), Decimal("105"), Decimal("99"), Decimal("101"))
    assert mop_reference_price(c0, "open") == Decimal("50")
    candles = [
        c0,
        OhlcCandle(st.replace(minute=0) + h, Decimal("101"), Decimal("130"), Decimal("100"), Decimal("125")),
    ]
    status, fields = compute_outcome_from_candles(
        model_key="market_on_publish",
        direction="LONG",
        entry_price=Decimal("100"),
        take_profit=Decimal("110"),
        stop_loss=Decimal("40"),
        signal_time=st,
        candles=candles,
        timeframe="1h",
        mop_reference="open",
    )
    assert status == "COMPLETE"
    assert fields["entry_fill_price"] == Decimal("50")


def test_multi_tp_long_same_bar():
    st = datetime(2025, 6, 1, 10, 0, tzinfo=timezone.utc)
    h = timedelta(hours=1)
    candles = [
        OhlcCandle(st, Decimal("100"), Decimal("105"), Decimal("99"), Decimal("102")),
        OhlcCandle(
            st + h,
            Decimal("102"),
            Decimal("150"),
            Decimal("101"),
            Decimal("140"),
        ),
    ]
    status, fields = compute_outcome_from_candles(
        model_key="market_on_publish",
        direction="LONG",
        entry_price=Decimal("100"),
        take_profit=None,
        stop_loss=Decimal("90"),
        signal_time=st,
        candles=candles,
        timeframe="1h",
        take_profit_levels=[Decimal("110"), Decimal("130")],
        sl_before_tp_same_bar=False,
    )
    assert status == "COMPLETE"
    assert len(fields["tp_hits"]) == 2
    assert fields["sl_hit"] is False


def test_no_candles_data_incomplete():
    status, fields = compute_outcome_from_candles(
        model_key="market_on_publish",
        direction="LONG",
        entry_price=Decimal("1"),
        take_profit=Decimal("2"),
        stop_loss=None,
        signal_time=datetime.now(timezone.utc),
        candles=[],
        timeframe="1h",
    )
    assert status == "DATA_INCOMPLETE"
    assert fields["error_detail"]["code"] == "no_candles"


def test_first_touch_long_entry_not_touched():
    st = datetime(2025, 6, 1, 10, 0, tzinfo=timezone.utc)
    h = timedelta(hours=1)
    candles = [
        OhlcCandle(st, Decimal("200"), Decimal("210"), Decimal("199"), Decimal("205")),
    ]
    status, fields = compute_outcome_from_candles(
        model_key="first_touch_limit",
        direction="LONG",
        entry_price=Decimal("100"),
        take_profit=Decimal("110"),
        stop_loss=Decimal("90"),
        signal_time=st,
        candles=candles,
        timeframe="1h",
    )
    assert status == "DATA_INCOMPLETE"
    assert fields["error_detail"]["code"] == "entry_not_touched"
