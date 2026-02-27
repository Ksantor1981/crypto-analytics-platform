"""Auth API tests using TestClient (sync)."""
import pytest
import uuid
import os
from fastapi.testclient import TestClient

os.environ["USE_SQLITE"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key-32-chars-minimum"
os.environ["SENTRY_DSN"] = ""


@pytest.fixture
def client():
    from app.main import app
    from app.core.database import engine, Base
    if engine and Base:
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
