"""Integration tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    import os
    os.environ["USE_SQLITE"] = "true"
    os.environ["SECRET_KEY"] = "test-secret-key-32-chars-minimum"
    from app.main import app
    return TestClient(app)

import uuid as _uuid
def _email(): return f"t_{_uuid.uuid4().hex[:10]}@test.com"


@pytest.fixture
def auth_token(client):
    
    email = _email()
    client.post("/api/v1/users/register", json={
        "email": email,
        "password": "TestPass123!",
        "confirm_password": "TestPass123!",
        "full_name": "Test User",
    })
    resp = client.post("/api/v1/users/login", json={
        "email": email,
        "password": "TestPass123!",
    })
    return resp.json()["access_token"]


class TestHealth:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "Crypto Analytics" in r.json()["message"]

    def test_api_status(self, client):
        r = client.get("/api/v1/status")
        assert r.status_code == 200
        assert r.json()["status"] == "operational"


class TestAuth:
    def test_register(self, client):
        
        email = _email()
        r = client.post("/api/v1/users/register", json={
            "email": email, "password": "NewPass123!",
            "confirm_password": "NewPass123!", "full_name": "New User",
        })
        assert r.status_code == 201
        assert r.json()["email"] == email

    def test_register_duplicate(self, client):
        
        email = _email()
        client.post("/api/v1/users/register", json={
            "email": email, "password": "Pass123!",
            "confirm_password": "Pass123!", "full_name": "Dup",
        })
        r = client.post("/api/v1/users/register", json={
            "email": email, "password": "Pass123!",
            "confirm_password": "Pass123!", "full_name": "Dup",
        })
        assert r.status_code in (400, 409)

    def test_login(self, client):
        
        email = _email()
        client.post("/api/v1/users/register", json={
            "email": email, "password": "Pass123!",
            "confirm_password": "Pass123!", "full_name": "Login",
        })
        r = client.post("/api/v1/users/login", json={"email": email, "password": "Pass123!"})
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_login_wrong_password(self, client):
        
        email = _email()
        client.post("/api/v1/users/register", json={
            "email": email, "password": "Pass123!",
            "confirm_password": "Pass123!", "full_name": "Wrong",
        })
        r = client.post("/api/v1/users/login", json={"email": email, "password": "WrongPass!"})
        assert r.status_code in (401, 400)

    def test_get_me_no_token_returns_error(self, client):
        r = client.get("/api/v1/users/me")
        assert r.status_code in (401, 403)

    def test_get_me_no_auth(self, client):
        r = client.get("/api/v1/users/me")
        assert r.status_code in (401, 403)


class TestChannels:
    def test_list_channels(self, client):
        r = client.get("/api/v1/channels/")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_has_seeded_channels(self, client):
        r = client.get("/api/v1/channels/")
        data = r.json()
        assert len(data) >= 5

    def test_get_channel_404(self, client):
        r = client.get("/api/v1/channels/99999")
        assert r.status_code == 404


class TestSignals:
    def test_list_signals(self, client):
        r = client.get("/api/v1/signals/")
        assert r.status_code == 200
        data = r.json()
        assert "signals" in data
        assert "total" in data

    def test_test_signals(self, client):
        r = client.get("/api/v1/test-signals")
        assert r.status_code == 200


class TestCollect:
    def test_validate_signal_404(self, client):
        r = client.get("/api/v1/collect/validate-signal/99999")
        assert r.status_code == 404
