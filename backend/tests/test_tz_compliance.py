"""
Тесты для соответствия ТЗ — критичные компоненты.
ТЗ: JWT auth, Stripe webhook, coverage, безопасность.
"""
import hashlib
import hmac
import json
import os
import time

import pytest
import uuid
from unittest.mock import patch, MagicMock


def _stripe_signature_header(body: bytes, secret: str) -> str:
    """Заголовок Stripe-Signature (как stripe.WebhookSignature: HMAC от \"{ts}.{payload_utf8}\")."""
    ts = int(time.time())
    payload_str = body.decode("utf-8")
    signed_payload = f"{ts}.{payload_str}"
    sig = hmac.new(
        secret.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"t={ts},v1={sig}"


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


_STRIPE_WEBHOOK_TEST_SECRET = "test_stripe_webhook_secret_for_unit_tests"


class TestStripeWebhook:
    """Stripe webhook (по ТЗ — обработка платежей)."""

    @pytest.fixture
    def client(self):
        os.environ["USE_SQLITE"] = "true"
        os.environ["SECRET_KEY"] = "test-secret-key-32-chars-minimum"
        os.environ["DEBUG"] = "true"
        os.environ["STRIPE_WEBHOOK_SECRET"] = _STRIPE_WEBHOOK_TEST_SECRET
        from app.main import app
        from app.core.database import Base, engine
        Base.metadata.create_all(bind=engine)
        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_stripe_webhook_checkout_completed(self, client):
        """Вебхук только с валидной подписью при заданном STRIPE_WEBHOOK_SECRET."""
        payload = {
            "id": "evt_checkout_unit_1",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "metadata": {"user_id": "1", "plan": "premium"},
                    "customer_email": "test@example.com",
                    "customer": "cus_test",
                }
            },
        }
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        sig = _stripe_signature_header(body, _STRIPE_WEBHOOK_TEST_SECRET)
        r = client.post(
            "/api/v1/stripe/webhook",
            content=body,
            headers={"Content-Type": "application/json", "Stripe-Signature": sig},
        )
        assert r.status_code == 200
        assert r.json().get("received") is True

    def test_stripe_webhook_rejects_bad_signature(self, client):
        payload = {"type": "checkout.session.completed", "data": {"object": {}}}
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        r = client.post(
            "/api/v1/stripe/webhook",
            content=body,
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "t=1,v1=deadbeef",
            },
        )
        assert r.status_code == 400

    def test_stripe_webhook_501_without_secret(self, client):
        prev = os.environ.pop("STRIPE_WEBHOOK_SECRET", None)
        try:
            body = json.dumps(
                {"type": "checkout.session.completed", "data": {"object": {}}},
                separators=(",", ":"),
            ).encode("utf-8")
            r = client.post(
                "/api/v1/stripe/webhook",
                content=body,
                headers={"Content-Type": "application/json"},
            )
            assert r.status_code == 501
        finally:
            if prev is not None:
                os.environ["STRIPE_WEBHOOK_SECRET"] = prev
            else:
                os.environ["STRIPE_WEBHOOK_SECRET"] = _STRIPE_WEBHOOK_TEST_SECRET

    def test_stripe_webhook_subscription_event(self, client):
        payload = {
            "id": "evt_sub_unit_1",
            "type": "customer.subscription.deleted",
            "data": {"object": {}},
        }
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        sig = _stripe_signature_header(body, _STRIPE_WEBHOOK_TEST_SECRET)
        r = client.post(
            "/api/v1/stripe/webhook",
            content=body,
            headers={"Content-Type": "application/json", "Stripe-Signature": sig},
        )
        assert r.status_code == 200

    def test_stripe_webhook_duplicate_event_id_returns_duplicate(self, client):
        """Повторная доставка того же event.id — без повторной обработки."""
        from app.core.stripe_webhook_dedup import clear_memory_dedup_for_tests

        clear_memory_dedup_for_tests()
        payload = {
            "id": "evt_idempotent_test_1",
            "type": "customer.subscription.deleted",
            "data": {"object": {}},
        }
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        sig = _stripe_signature_header(body, _STRIPE_WEBHOOK_TEST_SECRET)
        h = {"Content-Type": "application/json", "Stripe-Signature": sig}
        r1 = client.post("/api/v1/stripe/webhook", content=body, headers=h)
        assert r1.status_code == 200
        assert r1.json().get("received") is True
        assert r1.json().get("duplicate") is not True
        r2 = client.post("/api/v1/stripe/webhook", content=body, headers=h)
        assert r2.status_code == 200
        assert r2.json().get("duplicate") is True


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
