"""Admin signal-relations API."""
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
    import app.models.normalized_signal  # noqa: F401
    import app.models.raw_ingestion  # noqa: F401
    import app.models.signal_relation  # noqa: F401
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
            username=f"sr_{uuid.uuid4().hex[:6]}",
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


def test_list_relations_requires_filter(client, admin_headers):
    r = client.get("/api/v1/admin/signal-relations/", headers=admin_headers)
    assert r.status_code == 422


def test_list_relations_empty(client, admin_headers):
    r = client.get(
        "/api/v1/admin/signal-relations/?from_normalized_signal_id=1",
        headers=admin_headers,
    )
    assert r.status_code == 200
    assert r.json() == []


def test_post_relation_requires_admin(client, user_headers):
    r = client.post(
        "/api/v1/admin/signal-relations/",
        headers=user_headers,
        json={
            "from_normalized_signal_id": 1,
            "to_normalized_signal_id": 2,
            "relation_type": "update_to",
        },
    )
    assert r.status_code == 403


def test_post_relation_invalid_type_422(client, admin_headers):
    r = client.post(
        "/api/v1/admin/signal-relations/",
        headers=admin_headers,
        json={
            "from_normalized_signal_id": 1,
            "to_normalized_signal_id": 2,
            "relation_type": "invalid_type",
        },
    )
    assert r.status_code == 422


def test_post_relation_same_id_422(client, admin_headers):
    r = client.post(
        "/api/v1/admin/signal-relations/",
        headers=admin_headers,
        json={
            "from_normalized_signal_id": 1,
            "to_normalized_signal_id": 1,
            "relation_type": "duplicate_of",
        },
    )
    assert r.status_code == 422


def test_post_relation_missing_normals_404(client, admin_headers):
    r = client.post(
        "/api/v1/admin/signal-relations/",
        headers=admin_headers,
        json={
            "from_normalized_signal_id": 999998,
            "to_normalized_signal_id": 999999,
            "relation_type": "duplicate_of",
        },
    )
    assert r.status_code == 404

