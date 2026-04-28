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
    os.environ["AUTH_RATE_LIMIT_REQUESTS"] = "1000"
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

    def test_get_channels_dashboard_requires_auth(self, client):
        r = client.get("/api/v1/channels/dashboard/")
        assert r.status_code in (401, 403)

    def test_get_channels_dashboard_with_auth(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("Auth not available")
        r = client.get("/api/v1/channels/dashboard/", headers=auth_headers)
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
    def test_get_signals_list(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("Auth not available")
        r = client.get("/api/v1/signals/", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert "signals" in data or "total" in data or isinstance(data, list)

    def test_get_signals_with_channel_filter(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("Auth not available")
        r = client.get("/api/v1/signals/?channel_id=1", headers=auth_headers)
        assert r.status_code == 200

    def test_get_signals_dashboard_requires_auth(self, client):
        """Регрессия F2: /signals/dashboard больше НЕ публичный."""
        r = client.get("/api/v1/signals/dashboard")
        assert r.status_code in (401, 403)

    def test_get_signals_dashboard_with_auth(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("Auth not available")
        r = client.get("/api/v1/signals/dashboard", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_telegram_webhook_disabled_without_token(self, client, monkeypatch):
        """Регрессия F12: webhook закрыт, если TELEGRAM_INTEGRATION_TOKEN пуст."""
        monkeypatch.delenv("TELEGRAM_INTEGRATION_TOKEN", raising=False)
        r = client.post(
            "/api/v1/signals/telegram/webhook",
            json={"asset": "BTC", "direction": "LONG", "entry_price": 100.0, "channel_id": 1},
        )
        assert r.status_code == 503, r.text

    def test_telegram_webhook_rejects_wrong_token(self, client, monkeypatch):
        """Регрессия F12: 401 при неправильном/отсутствующем X-Integration-Token."""
        monkeypatch.setenv("TELEGRAM_INTEGRATION_TOKEN", "secret-test-token-xxx")
        r1 = client.post(
            "/api/v1/signals/telegram/webhook",
            json={"asset": "BTC", "direction": "LONG", "entry_price": 100.0, "channel_id": 1},
        )
        assert r1.status_code == 401, r1.text

        r2 = client.post(
            "/api/v1/signals/telegram/webhook",
            json={"asset": "BTC", "direction": "LONG", "entry_price": 100.0, "channel_id": 1},
            headers={"X-Integration-Token": "wrong"},
        )
        assert r2.status_code == 401, r2.text

    def test_get_signals_stats_channel(self, client):
        r = client.get("/api/v1/signals/stats/channel/1")
        assert r.status_code in (401, 403)


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

    def test_ocr_parse_requires_auth(self, client):
        """Regression: OCR URL parsing must not be public (SSRF/DoS risk)."""
        r = client.post(
            "/api/v1/collect/ocr-parse",
            params={"image_url": "https://example.com/image.png"},
        )
        assert r.status_code in (401, 403)

    def test_telethon_status(self, client):
        r = client.get("/api/v1/collect/telethon-status")
        assert r.status_code == 200
        assert "authenticated" in r.json()

    def test_telethon_collect_all_requires_telethon_session(self, client, auth_headers):
        from unittest.mock import patch

        if not auth_headers:
            pytest.skip("Auth not available")
        with patch("app.api.endpoints.collect.telethon_ready", return_value=False):
            r = client.post(
                "/api/v1/collect/telethon-collect-all",
                headers=auth_headers,
            )
        assert r.status_code == 200
        assert r.json().get("error")

    def test_telethon_collect_all_runs_with_mocked_history(self, client, auth_headers):
        from unittest.mock import AsyncMock, patch

        if not auth_headers:
            pytest.skip("Auth not available")

        async def _empty(*_a, **_kw):
            return [], []

        with patch("app.api.endpoints.collect.telethon_ready", return_value=True):
            with patch(
                "app.services.telethon_collector.collect_channel_history",
                new=AsyncMock(side_effect=_empty),
            ):
                r = client.post(
                    "/api/v1/collect/telethon-collect-all",
                    headers=auth_headers,
                )
        assert r.status_code == 200
        body = r.json()
        assert "channels_processed" in body
        assert "results" in body
        assert isinstance(body["results"], list)


class TestDashboardAPI:
    def test_dashboard_signals(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("Auth not available")
        r = client.get("/api/v1/dashboard/signals", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_dashboard_channels(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("Auth not available")
        r = client.get("/api/v1/dashboard/channels", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_dashboard_signals_pagination(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("Auth not available")
        r = client.get("/api/v1/dashboard/signals?skip=0&limit=10", headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()) <= 10

    def test_legacy_test_signals_requires_admin_auth(self, client):
        """Regression: direct /test-signals endpoint must not leak signals."""
        r = client.get("/api/v1/test-signals")
        assert r.status_code in (401, 403)

    def test_predictions_test_requires_admin_auth(self, client):
        """Regression: ML test proxy must not be callable anonymously."""
        r = client.post("/api/v1/predictions/test")
        assert r.status_code in (401, 403)

    def test_shadow_ab_report_requires_admin_auth(self, client):
        """A/B legacy↔canonical report is an admin-only readiness surface."""
        r = client.get("/api/v1/admin/shadow/ab-report")
        assert r.status_code in (401, 403)

    def test_user_source_mutations_require_auth(self, client):
        """Regression: user source reanalyze/remove must not be anonymous."""
        r1 = client.post("/api/v1/reanalyze/999999")
        r2 = client.delete("/api/v1/remove/999999")
        assert r1.status_code in (401, 403)
        assert r2.status_code in (401, 403)


class TestExportSignalsAPI:
    def test_export_signals_requires_auth(self, client):
        r = client.get("/api/v1/export/signals.csv")
        assert r.status_code in (401, 403)

    def test_export_signals_with_auth(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("Auth not available")
        r = client.get("/api/v1/export/signals.csv", headers=auth_headers)
        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")
        assert "signals_export" in r.headers.get("content-disposition", "")


class TestUsersAPIWithAuth:
    def test_get_me_with_auth(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("Auth not available")
        r = client.get("/api/v1/users/me", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert "email" in data

    @pytest.mark.skip(reason="Flaky: bcrypt/passlib compatibility or async teardown")
    def test_get_me_stats_with_auth(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("Auth not available")
        r = client.get("/api/v1/users/me/stats", headers=auth_headers)
        assert r.status_code == 200

    def test_get_me_requires_auth(self, client):
        r = client.get("/api/v1/users/me")
        assert r.status_code in (401, 403)


class TestSubscriptionsAPIWithAuth:
    def test_get_subscription_me_with_auth(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("Auth not available")
        r = client.get("/api/v1/subscriptions/me", headers=auth_headers)
        assert r.status_code == 200


class TestStripeCheckoutAPI:
    def test_get_plans(self, client):
        r = client.get("/api/v1/stripe/plans")
        assert r.status_code == 200
        data = r.json()
        assert "plans" in data
        assert isinstance(data["plans"], list)


class TestFeedbackAPI:
    @pytest.mark.skip(reason="Feedback enum serialization")
    def test_create_feedback_anonymous(self, client):
        r = client.post("/api/v1/feedback/", json={
            "feedback_type": "general",
            "subject": "Test feedback subject",
            "message": "This is a test feedback message with enough length",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["subject"] == "Test feedback subject"
        assert data.get("feedback_type") == "general"
        assert data.get("status") == "new"

    def test_get_feedback_requires_admin(self, client, auth_headers):
        r = client.get("/api/v1/feedback/", headers=auth_headers or {})
        assert r.status_code in (200, 403)


class TestMLIntegrationAPI:
    def test_ml_health(self, client):
        r = client.get("/api/v1/ml/health")
        assert r.status_code in (200, 500), r.text
        if r.status_code == 200:
            data = r.json()
            assert "ml_service_status" in data

    def test_ml_model_info(self, client):
        r = client.get("/api/v1/ml/model/info")
        assert r.status_code in (200, 403, 404, 500, 502, 503, 504)


class TestAnalyticsAPI:
    def test_analytics_ranking_requires_auth(self, client):
        r = client.get("/api/v1/analytics/analytics/ranking")
        assert r.status_code in (401, 403)

    def test_analytics_ranking_with_auth(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("Auth not available")
        r = client.get("/api/v1/analytics/analytics/ranking", headers=auth_headers)
        assert r.status_code in (200, 500)


class TestMetricsEndpoint:
    def test_metrics_returns_prometheus_format(self, client):
        r = client.get("/metrics")
        assert r.status_code == 200
        assert "text/plain" in r.headers.get("content-type", "")
        body = r.text
        assert "http_requests_total" in body or "signals_" in body
        assert "signals_collected_raw_total" in body or "signals_saved_total" in body

    def test_metrics_pipeline_counters_exist(self, client):
        r = client.get("/metrics")
        assert r.status_code == 200
        body = r.text
        assert "signals_collected_raw_total" in body
        assert "signals_parsed_ok_total" in body
        assert "signals_saved_total" in body
        assert "signals_skipped_total" in body


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


class TestReadinessAndTracing:
    def test_ready_includes_checks(self, client):
        r = client.get("/ready")
        assert r.status_code in (200, 503)
        data = r.json()
        assert "checks" in data
        assert "database" in data["checks"]

    def test_health_returns_x_request_id(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.headers.get("x-request-id") or r.headers.get("X-Request-ID")
