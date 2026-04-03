"""Admin execution-models API: RBAC, list, get by id/key."""
import uuid

import pytest
from fastapi.testclient import TestClient


def _seed_three(db):
    from app.models.execution_model import ExecutionModel

    db.query(ExecutionModel).delete()
    db.commit()

    rows = [
        ExecutionModel(
            model_key="market_on_publish",
            display_name="Market on publish",
            description="d1",
            fill_rule={"variant": "price_at_publish"},
            slippage_policy={},
            fee_policy={},
            expiry_policy={},
            is_active=True,
            sort_order=10,
        ),
        ExecutionModel(
            model_key="first_touch_limit",
            display_name="First touch limit",
            description="d2",
            fill_rule={"variant": "first_touch_entry_zone"},
            slippage_policy={},
            fee_policy={},
            expiry_policy={},
            is_active=True,
            sort_order=20,
        ),
        ExecutionModel(
            model_key="midpoint_entry",
            display_name="Midpoint entry",
            description="d3",
            fill_rule={"variant": "midpoint_of_entry_zone"},
            slippage_policy={},
            fee_policy={},
            expiry_policy={},
            is_active=False,
            sort_order=30,
        ),
    ]
    for r in rows:
        db.add(r)
    db.commit()


@pytest.fixture
def client():
    import os

    os.environ["USE_SQLITE"] = "true"
    os.environ["SECRET_KEY"] = "test-secret-key-32-chars-minimum"
    os.environ["DEBUG"] = "true"
    import app.models.execution_model  # noqa: F401
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
            username=f"e_{uuid.uuid4().hex[:6]}",
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


@pytest.fixture
def seeded_client(client):
    from app.core.database import SessionLocal

    db = SessionLocal()
    _seed_three(db)
    db.close()
    return client


def test_list_requires_admin(client, user_headers):
    r = client.get("/api/v1/admin/execution-models/", headers=user_headers)
    assert r.status_code == 403


def test_list_admin_active_only_default(seeded_client, admin_headers):
    r = seeded_client.get("/api/v1/admin/execution-models/", headers=admin_headers)
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 2
    keys = {x["model_key"] for x in body}
    assert keys == {"market_on_publish", "first_touch_limit"}


def test_list_include_inactive(seeded_client, admin_headers):
    r = seeded_client.get(
        "/api/v1/admin/execution-models/?active_only=false",
        headers=admin_headers,
    )
    assert r.status_code == 200
    assert len(r.json()) == 3


def test_get_by_id(seeded_client, admin_headers):
    lst = seeded_client.get("/api/v1/admin/execution-models/?active_only=false", headers=admin_headers)
    first_id = lst.json()[0]["id"]
    r = seeded_client.get(f"/api/v1/admin/execution-models/{first_id}", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["model_key"] == "market_on_publish"


def test_get_by_key(seeded_client, admin_headers):
    r = seeded_client.get(
        "/api/v1/admin/execution-models/by-key/midpoint_entry",
        headers=admin_headers,
    )
    assert r.status_code == 200
    assert r.json()["display_name"] == "Midpoint entry"
    assert r.json()["is_active"] is False


def test_get_404(seeded_client, admin_headers):
    r = seeded_client.get("/api/v1/admin/execution-models/999", headers=admin_headers)
    assert r.status_code == 404
