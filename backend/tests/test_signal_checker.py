"""Тесты для signal_checker: check_pending_signals с моком цены."""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from app.core.database import SessionLocal
from app.models.base import Base
from app.models.channel import Channel
from app.models.signal import Signal, SignalDirection, SignalStatus
from app.services.signal_checker import check_pending_signals


@pytest.fixture
def db_signal_checker():
    from app.core.database import engine
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def channel(db_signal_checker):
    import uuid
    uid = uuid.uuid4().hex[:8]
    ch = Channel(
        name=f"Test_{uid}",
        url=f"https://t.me/test_{uid}",
        username=f"test_{uid}",
        platform="telegram",
        is_active=True,
    )
    db_signal_checker.add(ch)
    db_signal_checker.commit()
    db_signal_checker.refresh(ch)
    return ch


@pytest.fixture
def pending_long_signal(db_signal_checker, channel):
    s = Signal(
        channel_id=channel.id,
        asset="BTC/USDT",
        symbol="BTCUSDT",
        direction=SignalDirection.LONG,
        entry_price=Decimal("50000"),
        tp1_price=Decimal("52000"),
        stop_loss=Decimal("48000"),
        status=SignalStatus.PENDING,
    )
    db_signal_checker.add(s)
    db_signal_checker.commit()
    db_signal_checker.refresh(s)
    return s


@pytest.fixture
def pending_short_signal(db_signal_checker, channel):
    s = Signal(
        channel_id=channel.id,
        asset="ETH/USDT",
        symbol="ETHUSDT",
        direction=SignalDirection.SHORT,
        entry_price=Decimal("3000"),
        tp1_price=Decimal("2800"),
        stop_loss=Decimal("3200"),
        status=SignalStatus.PENDING,
    )
    db_signal_checker.add(s)
    db_signal_checker.commit()
    db_signal_checker.refresh(s)
    return s


@pytest.mark.asyncio
async def test_check_pending_signals_tp_hit_long(db_signal_checker, pending_long_signal, channel):
    """LONG: текущая цена >= TP -> TP1_HIT."""
    with patch("app.services.signal_checker.get_current_price", new_callable=AsyncMock, return_value=52000.0):
        out = await check_pending_signals(db_signal_checker)
    assert out["checked"] >= 1
    assert out["updated"] >= 1
    db_signal_checker.refresh(pending_long_signal)
    assert pending_long_signal.status == SignalStatus.TP1_HIT
    assert pending_long_signal.is_successful is True


@pytest.mark.asyncio
async def test_check_pending_signals_sl_hit_long(db_signal_checker, pending_long_signal):
    """LONG: текущая цена <= SL -> SL_HIT."""
    with patch("app.services.signal_checker.get_current_price", new_callable=AsyncMock, return_value=47000.0):
        await check_pending_signals(db_signal_checker)
    db_signal_checker.refresh(pending_long_signal)
    assert pending_long_signal.status == SignalStatus.SL_HIT
    assert pending_long_signal.is_successful is False


@pytest.mark.asyncio
async def test_check_pending_signals_tp_hit_short(db_signal_checker, pending_short_signal):
    """SHORT: текущая цена <= TP -> TP1_HIT."""
    with patch("app.services.signal_checker.get_current_price", new_callable=AsyncMock, return_value=2750.0):
        await check_pending_signals(db_signal_checker)
    db_signal_checker.refresh(pending_short_signal)
    assert pending_short_signal.status == SignalStatus.TP1_HIT


@pytest.mark.asyncio
async def test_check_pending_signals_no_price(db_signal_checker, pending_long_signal):
    """Нет цены -> сигнал остаётся PENDING."""
    with patch("app.services.signal_checker.get_current_price", new_callable=AsyncMock, return_value=None):
        out = await check_pending_signals(db_signal_checker)
    assert out["updated"] == 0
    db_signal_checker.refresh(pending_long_signal)
    assert pending_long_signal.status == SignalStatus.PENDING
