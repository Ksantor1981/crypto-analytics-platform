"""Auth API tests using TestClient (sync)."""
import pytest
import uuid
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    import os
    os.environ["USE_SQLITE"] = "true"
    os.environ["SECRET_KEY"] = "test-secret-key-32-chars-minimum"
    from app.main import app
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
