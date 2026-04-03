"""Custom alerts Pro API (SQLite)."""
import uuid

import pytest
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


def test_custom_alert_templates_public(client):
    r = client.get("/api/v1/alerts/custom/templates")
    assert r.status_code == 200
    body = r.json()
    assert "templates" in body


def test_custom_alerts_require_pro(client):
    email = f"free_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/users/register",
        json={
            "email": email,
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
            "full_name": "Free",
        },
    )
    lr = client.post("/api/v1/users/login", json={"email": email, "password": "StrongPass123!"})
    token = lr.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    r = client.get("/api/v1/alerts/custom", headers=h)
    assert r.status_code == 403


def test_custom_alerts_crud_pro(client):
    from app.core.database import SessionLocal
    from app.models.user import User, SubscriptionPlan

    email = f"pro_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/users/register",
        json={
            "email": email,
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
            "full_name": "Pro User",
        },
    )
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == email).first()
        assert u is not None
        u.update_subscription_plan(SubscriptionPlan.PRO)
        db.commit()
    finally:
        db.close()

    lr = client.post("/api/v1/users/login", json={"email": email, "password": "StrongPass123!"})
    assert lr.status_code == 200, lr.text
    token = lr.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    payload = {
        "name": "High conf",
        "type": "signal_confidence",
        "conditions": {"confidence_threshold": 0.5},
        "actions": {"email_notification": True},
    }
    cr = client.post("/api/v1/alerts/custom", json=payload, headers=h)
    assert cr.status_code == 201, cr.text
    aid = cr.json()["data"]["id"]

    lst = client.get("/api/v1/alerts/custom", headers=h)
    assert lst.status_code == 200
    assert len(lst.json()) == 1

    pr = client.patch(
        f"/api/v1/alerts/custom/{aid}",
        json={"name": "Renamed"},
        headers=h,
    )
    assert pr.status_code == 200, pr.text
    assert pr.json()["name"] == "Renamed"

    dr = client.delete(f"/api/v1/alerts/custom/{aid}", headers=h)
    assert dr.status_code == 204

    lst2 = client.get("/api/v1/alerts/custom", headers=h)
    assert lst2.json() == []
