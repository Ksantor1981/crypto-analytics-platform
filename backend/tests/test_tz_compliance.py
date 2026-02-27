"""
Тесты для соответствия ТЗ — критичные компоненты.
ТЗ: JWT auth, Stripe webhook, coverage, безопасность.
"""
import pytest
import uuid
from unittest.mock import patch, MagicMock


class TestSecurityCore:
    """Безопасность: хэширование, JWT (по ТЗ)."""

    def test_password_hash_and_verify(self):
        from app.core.security import get_password_hash, verify_password
        pwd = "SecurePass123!"
        hashed = get_password_hash(pwd)
        assert hashed != pwd
        assert verify_password(pwd, hashed) is True
        assert verify_password("WrongPass", hashed) is False

    def test_create_and_verify_access_token(self):
        from app.core.security import create_access_token, verify_token
        data = {"sub": "123", "email": "test@example.com"}
        token = create_access_token(data)
        assert token
        payload = verify_token(token, "access")
        assert payload.get("sub") == "123"
        assert "exp" in payload


class TestCollectStatusEndpoints:
    """Collect API: telethon-status, bot-status (по ТЗ — сбор данных)."""

    @pytest.fixture
    def client(self):
        import os
        os.environ["USE_SQLITE"] = "true"
        os.environ["SECRET_KEY"] = "test-secret-key-32-chars-minimum"
        os.environ["DEBUG"] = "true"
        from app.main import app
        from app.core.database import Base, engine
        Base.metadata.create_all(bind=engine)
        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_telethon_status(self, client):
        r = client.get("/api/v1/collect/telethon-status")
        assert r.status_code == 200
        data = r.json()
        assert "authenticated" in data
        assert "how_to_auth" in data

    def test_bot_status(self, client):
        from unittest.mock import AsyncMock
        with patch("app.services.telegram_bot.check_bot_access_to_channels", new_callable=AsyncMock) as mock_check:
            mock_check.return_value = {"channels": [], "accessible": 0}
            r = client.get("/api/v1/collect/bot-status")
        assert r.status_code == 200


class TestStripeWebhook:
    """Stripe webhook (по ТЗ — обработка платежей)."""

    @pytest.fixture
    def client(self):
        import os
        os.environ["USE_SQLITE"] = "true"
        os.environ["SECRET_KEY"] = "test-secret-key-32-chars-minimum"
        os.environ["DEBUG"] = "true"
        from app.main import app
        from app.core.database import Base, engine
        Base.metadata.create_all(bind=engine)
        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_stripe_webhook_checkout_completed(self, client):
        """Без STRIPE_WEBHOOK_SECRET используется json.loads."""
        payload = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "metadata": {"user_id": "1", "plan": "premium"},
                    "customer_email": "test@example.com",
                    "customer": "cus_test",
                }
            }
        }
        import json
        r = client.post(
            "/api/v1/stripe/webhook",
            content=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == 200
        assert r.json().get("received") is True

    def test_stripe_webhook_subscription_event(self, client):
        payload = {
            "type": "customer.subscription.deleted",
            "data": {"object": {}}
        }
        import json
        r = client.post(
            "/api/v1/stripe/webhook",
            content=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == 200


class TestRootAndHealth:
    """Корневые и health эндпоинты."""

    @pytest.fixture
    def client(self):
        import os
        os.environ["USE_SQLITE"] = "true"
        os.environ["SECRET_KEY"] = "test-secret-key-32-chars-minimum"
        from app.main import app
        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert "message" in data
        assert "version" in data

    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code in (200, 503)

    def test_ready(self, client):
        r = client.get("/ready")
        assert r.status_code in (200, 503)


class TestUserServiceTZ:
    """UserService: create_user, get_user_by_email (по ТЗ — auth)."""

    def test_create_user_and_get_by_email(self):
        from app.core.database import SessionLocal
        from app.models.base import Base
        from app.core.database import engine
        from app.services.user_service import UserService
        from app.schemas.user import UserCreate

        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            email = f"tz_{uuid.uuid4().hex[:8]}@example.com"
            user_data = UserCreate(
                email=email,
                password="StrongPass123!",
                confirm_password="StrongPass123!",
                full_name="TZ Test",
            )
            svc = UserService(db)
            user = svc.create_user(user_data)
            assert user.id
            assert user.email == email

            found = svc.get_user_by_email(email)
            assert found.id == user.id
            assert svc.is_email_available(email) is False
            assert svc.is_email_available("nonexistent@x.com") is True
        finally:
            db.close()
