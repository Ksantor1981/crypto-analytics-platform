"""
Интеграционные тесты для app/services и app/models.
Цель: повысить покрытие до 40%+ по services и models.
"""
import pytest
from datetime import datetime
from decimal import Decimal
from fastapi import HTTPException

from app.core.database import SessionLocal, engine
from app.models.base import Base
from app.models.channel import Channel
from app.models.signal import Signal, SignalDirection, SignalStatus
from app.models.user import User
from app.services.channel_service import ChannelService
from app.services.signal_service import SignalService
from app.services.metrics_calculator import recalculate_channel_metrics, recalculate_all_channels
from app.schemas.signal import SignalCreate, SignalFilterParams


@pytest.fixture(scope="module")
def db_engine():
    """Создаём таблицы для тестов."""
    Base.metadata.create_all(bind=engine)
    yield engine


@pytest.fixture
def db_session(db_engine):
    """Сессия БД с откатом после теста."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def sample_user(db_session):
    """Пользователь для тестов."""
    user = User(
        email="test_coverage@example.com",
        username="test_coverage",
        full_name="Test User",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_channel(db_session, sample_user):
    """Канал для тестов."""
    ch = Channel(
        name="Test Channel",
        username="test_channel_coverage",
        url="https://t.me/test_channel_coverage",
        platform="telegram",
        owner_id=sample_user.id,
    )
    db_session.add(ch)
    db_session.commit()
    db_session.refresh(ch)
    return ch


@pytest.fixture
def sample_signals(db_session, sample_channel):
    """Сигналы для тестов метрик."""
    signals = []
    for i in range(5):
        s = Signal(
            channel_id=sample_channel.id,
            asset="BTC/USDT",
            symbol="BTCUSDT",
            direction=SignalDirection.LONG,
            entry_price=Decimal("50000"),
            tp1_price=Decimal("55000"),
            stop_loss=Decimal("48000"),
            status=SignalStatus.TP1_HIT if i < 3 else SignalStatus.SL_HIT,
            is_successful=(i < 3),
            profit_loss_percentage=Decimal("10") if i < 3 else Decimal("-2"),
            profit_loss_absolute=Decimal("10") if i < 3 else Decimal("-2"),
            message_timestamp=datetime.utcnow(),
        )
        db_session.add(s)
        signals.append(s)
    db_session.commit()
    for s in signals:
        db_session.refresh(s)
    return signals


# --- ChannelService ---
class TestChannelServiceIntegration:
    def test_get_channels_returns_list(self, db_session):
        """Возвращает список (БД может быть с seed)."""
        channels = ChannelService.get_channels(db_session, limit=10)
        assert isinstance(channels, list)

    def test_get_channels_with_data(self, db_session, sample_channel):
        """В выборке есть каналы и созданный sample_channel (limit достаточный при seed)."""
        channels = ChannelService.get_channels(db_session, limit=100)
        assert len(channels) >= 1
        assert any(c.id == sample_channel.id for c in channels)

    def test_get_channels_filter_platform(self, db_session, sample_channel):
        channels = ChannelService.get_channels(db_session, platform="telegram")
        assert all(c.platform == "telegram" for c in channels)

    def test_get_channel_by_id_success(self, db_session, sample_channel):
        ch = ChannelService.get_channel_by_id(db_session, sample_channel.id)
        assert ch.id == sample_channel.id
        assert ch.name == sample_channel.name

    def test_get_channel_by_id_not_found(self, db_session):
        with pytest.raises(HTTPException) as exc:
            ChannelService.get_channel_by_id(db_session, 999999)
        assert exc.value.status_code == 404


# --- SignalService ---
class TestSignalServiceIntegration:
    def test_create_signal_success(self, db_session, sample_channel):
        svc = SignalService(db_session)
        signal_data = SignalCreate(
            channel_id=sample_channel.id,
            asset="ETH/USDT",
            direction=SignalDirection.LONG,
            entry_price=2000.0,
            tp1_price=2200.0,
            stop_loss=1900.0,
        )
        sig = svc.create_signal(signal_data)
        assert sig.id is not None
        assert sig.asset == "ETH/USDT"
        assert sig.entry_price == Decimal("2000")
        assert sig.risk_reward_ratio is not None

    def test_create_signal_channel_not_found(self, db_session):
        svc = SignalService(db_session)
        signal_data = SignalCreate(
            channel_id=999999,
            asset="BTC/USDT",
            direction=SignalDirection.LONG,
            entry_price=50000.0,
        )
        with pytest.raises(HTTPException) as exc:
            svc.create_signal(signal_data)
        assert exc.value.status_code == 404

    def test_get_signal_by_id_none(self, db_session):
        svc = SignalService(db_session)
        assert svc.get_signal_by_id(999999) is None

    def test_get_signals_empty_filters(self, db_session):
        svc = SignalService(db_session)
        signals, total = svc.get_signals(limit=10)
        assert isinstance(signals, list)
        assert total >= 0

    def test_get_signals_with_channel_filter(self, db_session, sample_channel, sample_signals):
        svc = SignalService(db_session)
        filters = SignalFilterParams(channel_id=sample_channel.id)
        signals, total = svc.get_signals(limit=100, filters=filters)
        assert total >= 5
        assert all(s.channel_id == sample_channel.id for s in signals)

    def test_get_signal_stats_empty(self, db_session):
        svc = SignalService(db_session)
        filters = SignalFilterParams(channel_id=999999)
        stats = svc.get_signal_stats(filters)
        assert stats.total_signals == 0
        assert stats.successful_signals == 0

    def test_get_signal_stats_with_data(self, db_session, sample_channel, sample_signals):
        svc = SignalService(db_session)
        stats = svc.get_signal_stats(SignalFilterParams(channel_id=sample_channel.id))
        assert stats.total_signals == 5
        assert stats.successful_signals == 3

    def test_get_channel_stats(self, db_session, sample_channel, sample_signals):
        svc = SignalService(db_session)
        ch_stats = svc.get_channel_stats(sample_channel.id, days=365)
        assert ch_stats.channel_id == sample_channel.id


# --- MetricsCalculator ---
class TestMetricsCalculatorIntegration:
    def test_recalculate_channel_metrics_not_found(self, db_session):
        result = recalculate_channel_metrics(db_session, 999999)
        assert "error" in result
        assert result["error"] == "Channel not found"

    def test_recalculate_channel_metrics_success(self, db_session, sample_channel, sample_signals):
        result = recalculate_channel_metrics(db_session, sample_channel.id)
        assert "error" not in result
        assert result["total_signals"] == 5
        assert result["resolved"] == 5
        assert result["hits"] == 3
        assert result["accuracy"] == 60.0  # 3/5 * 100

    def test_recalculate_all_channels(self, db_session, sample_channel):
        results = recalculate_all_channels(db_session)
        assert isinstance(results, list)
        assert len(results) >= 1


# --- User Service (базовые сценарии) ---
class TestUserServiceIntegration:
    def test_user_service_authenticate_fail(self, db_session):
        from app.services.user_service import UserService
        svc = UserService(db_session)
        user = svc.authenticate("nonexistent@test.com", "wrong")
        assert user is None
