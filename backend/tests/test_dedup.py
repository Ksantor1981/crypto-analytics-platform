"""Тесты для dedup: signal_exists, cleanup_duplicates."""
import pytest
import uuid
from decimal import Decimal

from app.core.database import engine, SessionLocal
from app.models.base import Base
from app.models.channel import Channel
from app.models.signal import Signal, SignalDirection
from app.services.dedup import signal_exists, cleanup_duplicates, content_fingerprint


@pytest.fixture
def db_dedup():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def ch(db_dedup):
    uid = uuid.uuid4().hex[:8]
    c = Channel(name=f"DedupTest_{uid}", url=f"https://t.me/dedup_{uid}", username=f"dedup_{uid}", platform="telegram", is_active=True)
    db_dedup.add(c)
    db_dedup.commit()
    db_dedup.refresh(c)
    return c


def test_signal_exists_empty(db_dedup, ch):
    assert signal_exists(db_dedup, ch.id, "BTC LONG 50k") is False


def test_signal_exists_after_add(db_dedup, ch):
    text = "BTC LONG entry 50000 tp 52000 sl 48000"
    s = Signal(
        channel_id=ch.id,
        asset="BTC/USDT",
        symbol="BTCUSDT",
        direction=SignalDirection.LONG,
        entry_price=Decimal("50000"),
        original_text=text,
        content_fingerprint=content_fingerprint(text),
        status="PENDING",
    )
    db_dedup.add(s)
    db_dedup.commit()
    assert signal_exists(db_dedup, ch.id, text) is True
    # пробелы/регистр после нормализации — тот же fingerprint
    assert signal_exists(db_dedup, ch.id, "  " + text.upper() + "  ") is True


def test_cleanup_duplicates_empty(db_dedup):
    assert cleanup_duplicates(db_dedup) == 0


def test_cleanup_duplicates_keeps_one(db_dedup, ch):
    text = "Same signal text"
    for _ in range(3):
        s = Signal(
            channel_id=ch.id,
            asset="BTC/USDT",
            symbol="BTCUSDT",
            direction=SignalDirection.LONG,
            entry_price=Decimal("50000"),
            original_text=text,
            status="PENDING",
        )
        db_dedup.add(s)
    db_dedup.commit()
    before = db_dedup.query(Signal).filter(Signal.channel_id == ch.id).count()
    assert before == 3
    deleted = cleanup_duplicates(db_dedup)
    assert deleted == 2
    after = db_dedup.query(Signal).filter(Signal.channel_id == ch.id).count()
    assert after == 1
