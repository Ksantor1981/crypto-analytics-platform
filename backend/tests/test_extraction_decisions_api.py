"""Admin extraction-decisions: RBAC, валидация override."""
import uuid

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    import os

    os.environ["USE_SQLITE"] = "true"
    os.environ["SECRET_KEY"] = "test-secret-key-32-chars-minimum"
    os.environ["DEBUG"] = "true"
    import app.models.extraction  # noqa: F401
    import app.models.extraction_decision  # noqa: F401
    import app.models.raw_ingestion  # noqa: F401
    from app.core.database import Base, engine
    from app.main import app as fastapi_app

    Base.metadata.create_all(bind=engine)
    return TestClient(fastapi_app)


@pytest.fixture
def admin_headers(client):
    from app.core.database import SessionLocal
    from app.core.security import get_password_hash
    from app.models.user import User, UserRole

    email = f"adm_{uuid.uuid4().hex[:8]}@example.com"
    db = SessionLocal()
    db.add(
        User(
            email=email,
            username=f"d_{uuid.uuid4().hex[:6]}",
            hashed_password=get_password_hash("StrongPass123!"),
            role=UserRole.ADMIN,
            is_active=True,
        )
    )
    db.commit()
    db.close()
    r = client.post("/api/v1/users/login", json={"email": email, "password": "StrongPass123!"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def user_headers(client):
    email = f"u_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/users/register",
        json={
            "email": email,
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
            "full_name": "U",
        },
    )
    r = client.post("/api/v1/users/login", json={"email": email, "password": "StrongPass123!"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_list_decisions_requires_admin(client, user_headers):
    r = client.get("/api/v1/admin/extraction-decisions/?raw_event_id=1", headers=user_headers)
    assert r.status_code == 403


def test_list_decisions_admin_ok_empty(client, admin_headers):
    # id вне типичных фикстур (общий SQLite-файл между тестами)
    r = client.get(
        "/api/v1/admin/extraction-decisions/?raw_event_id=999999999",
        headers=admin_headers,
    )
    assert r.status_code == 200
    assert r.json() == []


def test_override_invalid_type_422(client, admin_headers):
    r = client.post(
        "/api/v1/admin/extraction-decisions/override",
        headers=admin_headers,
        json={"extraction_id": 1, "decision_type": "not_a_valid_label"},
    )
    assert r.status_code == 422


def test_override_missing_extraction_404(client, admin_headers):
    r = client.post(
        "/api/v1/admin/extraction-decisions/override",
        headers=admin_headers,
        json={"extraction_id": 999999, "decision_type": "noise"},
    )
    assert r.status_code == 404
