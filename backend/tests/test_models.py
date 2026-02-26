"""Tests for data models and schemas."""
import pytest


class TestChannelModel:
    def test_import(self):
        from app.models.channel import Channel
        assert Channel.__tablename__ == "channels"

    def test_fields(self):
        from app.models.channel import Channel
        cols = {c.name for c in Channel.__table__.columns}
        for f in ["id", "name", "username", "url", "platform", "accuracy", "signals_count", "status"]:
            assert f in cols, f"Missing field: {f}"


class TestSignalModel:
    def test_import(self):
        from app.models.signal import Signal
        assert Signal.__tablename__ == "signals"

    def test_fields(self):
        from app.models.signal import Signal
        cols = {c.name for c in Signal.__table__.columns}
        for f in ["id", "channel_id", "asset", "direction", "entry_price", "status", "confidence_score"]:
            assert f in cols

    def test_status_enum(self):
        from app.models.signal import SignalStatus
        assert "PENDING" in [s.value for s in SignalStatus]
        assert "TP1_HIT" in [s.value for s in SignalStatus]
        assert "SL_HIT" in [s.value for s in SignalStatus]

    def test_direction_enum(self):
        from app.models.signal import SignalDirection
        assert "LONG" in [d.value for d in SignalDirection]
        assert "SHORT" in [d.value for d in SignalDirection]


class TestUserModel:
    def test_import(self):
        from app.models.user import User
        assert User.__tablename__ == "users"

    def test_role_enum(self):
        from app.models.user import UserRole
        roles = [r.value for r in UserRole]
        assert "FREE_USER" in roles


class TestSchemas:
    def test_channel_schema(self):
        from app.schemas.channel import ChannelCreate, ChannelResponse
        ch = ChannelCreate(name="Test", url="https://t.me/test", platform="telegram")
        assert ch.name == "Test"

    def test_signal_schema(self):
        from app.schemas.signal import SignalResponse, SignalWithChannel
        assert hasattr(SignalWithChannel, 'model_fields')
        assert "channel_name" in SignalWithChannel.model_fields

    def test_user_schema(self):
        from app.schemas.user import UserCreate
        u = UserCreate(email="t@test.com", password="Pass1!", confirm_password="Pass1!")
        assert u.email == "t@test.com"


class TestConfig:
    def test_settings(self):
        from app.core.config import get_settings
        s = get_settings()
        assert s.PROJECT_NAME == "Crypto Analytics Platform"
        assert s.VERSION == "1.0.0"

    def test_cors_not_wildcard(self):
        from app.core.config import get_settings
        s = get_settings()
        assert "*" not in s.BACKEND_CORS_ORIGINS

    def test_debug_default(self):
        from app.core.config import get_settings
        s = get_settings()
        assert isinstance(s.DEBUG, bool)
