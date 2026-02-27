"""Tests for API endpoints — channels, signals, subscriptions, collect."""
import pytest
import uuid
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    import os
    os.environ["USE_SQLITE"] = "true"
    os.environ["SECRET_KEY"] = "test-secret-key-32-chars-minimum"
    os.environ["DEBUG"] = "true"
    from app.main import app
    from app.core.database import SessionLocal, Base, engine
    Base.metadata.create_all(bind=engine)
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Register, login, return Authorization header."""
    email = f"api_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/v1/users/register", json={
        "email": email, "password": "StrongPass123!",
        "confirm_password": "StrongPass123!", "full_name": "API Test",
    })
    r = client.post("/api/v1/users/login", json={"email": email, "password": "StrongPass123!"})
    token = r.json().get("access_token")
    return {"Authorization": f"Bearer {token}"} if token else {}


class TestChannelsAPI:
    def test_get_channels_list(self, client):
        r = client.get("/api/v1/channels/")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_channels_dashboard(self, client):
        r = client.get("/api/v1/channels/dashboard/")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_channel_404(self, client):
        r = client.get("/api/v1/channels/999999")
        assert r.status_code == 404
        assert "not found" in r.json().get("detail", "").lower()

    def test_get_channel_with_valid_id(self, client):
        r = client.get("/api/v1/channels/")
        channels = r.json()
        if channels:
            ch_id = channels[0]["id"]
            r2 = client.get(f"/api/v1/channels/{ch_id}")
            assert r2.status_code == 200
            assert r2.json()["id"] == ch_id
        else:
            r2 = client.get("/api/v1/channels/1")
            # May 404 if no seed data
            assert r2.status_code in (200, 404)

    def test_create_channel_requires_auth(self, client):
        r = client.post("/api/v1/channels/", json={
            "name": "Test", "url": "https://t.me/test", "platform": "telegram"
        })
        assert r.status_code in (401, 403, 422)


class TestSignalsAPI:
    def test_get_signals_list(self, client):
        r = client.get("/api/v1/signals/")
        assert r.status_code == 200
        data = r.json()
        assert "signals" in data or "total" in data or isinstance(data, list)

    def test_get_signals_with_channel_filter(self, client):
        r = client.get("/api/v1/signals/?channel_id=1")
        assert r.status_code == 200


class TestSubscriptionsAPI:
    def test_get_plans_public(self, client):
        r = client.get("/api/v1/subscriptions/plans")
        assert r.status_code == 200
        plans = r.json()
        assert isinstance(plans, list)
        assert len(plans) >= 1
        if plans:
            p = plans[0]
            assert "name" in p or "plan" in p
            assert "price_monthly" in p or "features" in p or "description" in p


class TestCollectAPI:
    def test_recalculate_requires_auth(self, client):
        r = client.post("/api/v1/collect/recalculate-metrics")
        assert r.status_code in (401, 403, 422)


class TestMetricsCalculator:
    def test_recalculate_callable(self):
        from app.services.metrics_calculator import recalculate_all_channels
        assert callable(recalculate_all_channels)


class TestChannelService:
    def test_get_channel_by_id_raises_404(self, client):
        from app.core.database import SessionLocal
        from app.services.channel_service import ChannelService
        from fastapi import HTTPException
        db = SessionLocal()
        try:
            with pytest.raises(HTTPException) as exc:
                ChannelService.get_channel_by_id(db, 999999)
            assert exc.value.status_code == 404
        finally:
            db.close()


class TestSignalService:
    def test_get_signal_stats_empty(self, client):
        from app.core.database import SessionLocal
        from app.services.signal_service import SignalService
        from app.schemas.signal import SignalFilterParams
        db = SessionLocal()
        try:
            svc = SignalService(db)
            stats = svc.get_signal_stats(SignalFilterParams(channel_id=999999))
            assert stats.total_signals == 0
            assert stats.successful_signals == 0
        finally:
            db.close()


class TestSchemas:
    def test_channel_schema(self):
        from app.schemas.channel import ChannelResponse
        data = {
            "id": 1, "name": "Test", "url": "https://t.me/t", "platform": "telegram",
            "username": "t", "created_at": "2024-01-01T00:00:00"
        }
        ch = ChannelResponse.model_validate(data)
        assert ch.id == 1
        assert ch.name == "Test"

    def test_signal_filter_params(self):
        from app.schemas.signal import SignalFilterParams
        p = SignalFilterParams(channel_id=1, asset="BTC/USDT")
        assert p.channel_id == 1
        assert p.asset == "BTC/USDT"


class TestHistoricalValidator:
    def test_import(self):
        from app.services.historical_validator import validate_all_signals, validate_signal_historically
        assert callable(validate_all_signals)
        assert callable(validate_signal_historically)
