"""Auth API tests using TestClient (sync)."""
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
    from app.core.database import Base, engine
    Base.metadata.create_all(bind=engine)
    return TestClient(app)


def test_register_new_user_success(client):
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/v1/users/register", json={
        "email": email, "password": "StrongPass123!",
        "confirm_password": "StrongPass123!", "full_name": "Test User",
    })
    assert r.status_code == 201, f"Got {r.status_code}: {r.text}"
    assert r.json()["email"] == email


def test_register_existing_user_fails(client):
    email = f"dup_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/v1/users/register", json={
        "email": email, "password": "StrongPass123!",
        "confirm_password": "StrongPass123!", "full_name": "Dup",
    })
    r = client.post("/api/v1/users/register", json={
        "email": email, "password": "StrongPass123!",
        "confirm_password": "StrongPass123!", "full_name": "Dup",
    })
    assert r.status_code in (400, 409)


def test_me_limits_requires_auth(client):
    r = client.get("/api/v1/users/me/limits")
    assert r.status_code == 403


def test_me_limits_after_register_and_login(client):
    email = f"lim_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/v1/users/register", json={
        "email": email, "password": "StrongPass123!",
        "confirm_password": "StrongPass123!", "full_name": "Lim User",
    })
    lr = client.post("/api/v1/users/login", json={"email": email, "password": "StrongPass123!"})
    assert lr.status_code == 200, lr.text
    token = lr.json()["access_token"]
    r = client.get(
        "/api/v1/users/me/limits",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "plan" in body
    assert "channels_limit" in body
    assert "channels_used" in body
    assert "can_add_channel" in body
