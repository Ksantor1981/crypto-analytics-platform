"""Admin extractions API: RBAC, флаг EXTRACTION_PIPELINE_ENABLED, 404 без версии."""
from unittest.mock import MagicMock, patch

import pytest
import uuid
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
    u = User(
        email=email,
        username=f"e_{uuid.uuid4().hex[:6]}",
        hashed_password=get_password_hash("StrongPass123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(u)
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


def test_run_extraction_pipeline_off_503(client, admin_headers):
    r = client.post(
        "/api/v1/admin/extractions/run-for-raw-event/1",
        headers=admin_headers,
    )
    assert r.status_code == 503
    assert "EXTRACTION_PIPELINE" in r.json().get("detail", "")


def test_run_extraction_requires_admin(client, user_headers):
    with patch(
        "app.api.endpoints.extractions.get_settings",
        return_value=MagicMock(EXTRACTION_PIPELINE_ENABLED=True),
    ):
        r = client.post(
            "/api/v1/admin/extractions/run-for-raw-event/1",
            headers=user_headers,
        )
    assert r.status_code == 403


def test_run_extraction_404_when_no_message_version(client, admin_headers):
    fake_mv = MagicMock()
    fake_mv.id = 99
    with patch(
        "app.api.endpoints.extractions.get_settings",
        return_value=MagicMock(EXTRACTION_PIPELINE_ENABLED=True),
    ):
        with patch(
            "app.api.endpoints.extractions.extraction_service.resolve_message_version_for_raw_event",
            return_value=None,
        ):
            r = client.post(
                "/api/v1/admin/extractions/run-for-raw-event/1",
                headers=admin_headers,
            )
    assert r.status_code == 404


def test_list_extractions_requires_admin(client, user_headers):
    r = client.get("/api/v1/admin/extractions/?raw_event_id=1", headers=user_headers)
    assert r.status_code == 403
