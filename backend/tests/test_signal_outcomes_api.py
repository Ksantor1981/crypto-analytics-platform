"""Admin signal-outcomes: ensure slots, list, RBAC."""
import uuid

import pytest
from fastapi.testclient import TestClient


def _seed_execution_models(db):
    from app.models.execution_model import ExecutionModel
    from app.models.signal_outcome import SignalOutcome

    db.query(SignalOutcome).delete()
    db.query(ExecutionModel).delete()
    db.commit()
    for spec in (
        ("market_on_publish", "MOP", True, 10),
        ("first_touch_limit", "FTL", True, 20),
        ("midpoint_entry", "MID", False, 30),
    ):
        db.add(
            ExecutionModel(
                model_key=spec[0],
                display_name=spec[1],
                description="t",
                fill_rule={},
                slippage_policy={},
                fee_policy={},
                expiry_policy={},
                is_active=spec[2],
                sort_order=spec[3],
            )
        )
    db.commit()


@pytest.fixture
def client():
    import os

    os.environ["USE_SQLITE"] = "true"
    os.environ["SECRET_KEY"] = "test-secret-key-32-chars-minimum"
    os.environ["DEBUG"] = "true"
    import app.models.execution_model  # noqa: F401
    import app.models.extraction  # noqa: F401
    import app.models.extraction_decision  # noqa: F401
    import app.models.normalized_signal  # noqa: F401
    import app.models.raw_ingestion  # noqa: F401
    import app.models.review_label  # noqa: F401
    import app.models.signal_outcome  # noqa: F401
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
            username=f"o_{uuid.uuid4().hex[:6]}",
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
def ns_with_exec(client):
    from app.core.database import SessionLocal

    from test_normalized_signals_api import _insert_min_normalized_chain

    db = SessionLocal()
    _seed_execution_models(db)
    db.close()
    _, ns_id = _insert_min_normalized_chain()
    return ns_id


def test_list_requires_admin(client, user_headers):
    r = client.get("/api/v1/admin/signal-outcomes/?normalized_signal_id=1", headers=user_headers)
    assert r.status_code == 403


def test_ensure_404(client, admin_headers):
    r = client.post(
        "/api/v1/admin/signal-outcomes/ensure/999999999",
        headers=admin_headers,
    )
    assert r.status_code == 404


def test_ensure_for_raw_event(client, admin_headers):
    from app.core.database import SessionLocal
    from test_normalized_signals_api import _insert_min_normalized_chain

    db = SessionLocal()
    _seed_execution_models(db)
    db.close()
    raw_id, _ = _insert_min_normalized_chain()
    r = client.post(
        f"/api/v1/admin/signal-outcomes/ensure-for-raw-event/{raw_id}",
        headers=admin_headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["raw_event_id"] == raw_id
    assert body["normalized_signal_count"] == 1
    assert body["created_total"] == 2

    r404 = client.post(
        "/api/v1/admin/signal-outcomes/ensure-for-raw-event/999999999",
        headers=admin_headers,
    )
    assert r404.status_code == 404


def test_ensure_and_list(client, admin_headers, ns_with_exec):
    ns_id = ns_with_exec
    r = client.post(
        f"/api/v1/admin/signal-outcomes/ensure/{ns_id}",
        headers=admin_headers,
    )
    assert r.status_code == 200, r.text
    assert r.json() == {"normalized_signal_id": ns_id, "created": 2}

    r2 = client.get(
        f"/api/v1/admin/signal-outcomes/?normalized_signal_id={ns_id}",
        headers=admin_headers,
    )
    assert r2.status_code == 200
    body = r2.json()
    assert len(body) == 2
    keys = {x["execution_model_key"] for x in body}
    assert keys == {"market_on_publish", "first_touch_limit"}
    assert all(x["outcome_status"] == "PENDING" for x in body)

    r3 = client.post(
        f"/api/v1/admin/signal-outcomes/ensure/{ns_id}",
        headers=admin_headers,
    )
    assert r3.status_code == 200
    assert r3.json()["created"] == 0


def test_get_by_id(client, admin_headers, ns_with_exec):
    ns_id = ns_with_exec
    client.post(f"/api/v1/admin/signal-outcomes/ensure/{ns_id}", headers=admin_headers)
    lst = client.get(
        f"/api/v1/admin/signal-outcomes/?normalized_signal_id={ns_id}",
        headers=admin_headers,
    )
    oid = lst.json()[0]["id"]
    r = client.get(f"/api/v1/admin/signal-outcomes/{oid}", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["normalized_signal_id"] == ns_id


def test_get_outcome_404(client, admin_headers):
    r = client.get("/api/v1/admin/signal-outcomes/999999999", headers=admin_headers)
    assert r.status_code == 404


def test_recalculate_disabled_returns_503(client, admin_headers, ns_with_exec):
    ns_id = ns_with_exec
    client.post(f"/api/v1/admin/signal-outcomes/ensure/{ns_id}", headers=admin_headers)
    oid = client.get(
        f"/api/v1/admin/signal-outcomes/?normalized_signal_id={ns_id}",
        headers=admin_headers,
    ).json()[0]["id"]
    r = client.post(
        f"/api/v1/admin/signal-outcomes/{oid}/recalculate",
        headers=admin_headers,
    )
    assert r.status_code == 503


def test_recalculate_with_mock_candles(monkeypatch, client, admin_headers, ns_with_exec):
    from datetime import datetime, timedelta, timezone
    from decimal import Decimal

    from app.core.database import SessionLocal
    from app.models.normalized_signal import NormalizedSignal
    from app.models.raw_ingestion import RawEvent
    from app.services.outcome_candle_engine import OhlcCandle

    monkeypatch.setenv("OUTCOME_RECALC_ENABLED", "true")

    ns_id = ns_with_exec
    client.post(f"/api/v1/admin/signal-outcomes/ensure/{ns_id}", headers=admin_headers)

    st = datetime(2025, 6, 1, 10, 30, tzinfo=timezone.utc)
    db = SessionLocal()
    ns = db.query(NormalizedSignal).filter(NormalizedSignal.id == ns_id).first()
    re = db.query(RawEvent).filter(RawEvent.id == ns.raw_event_id).first()
    re.first_seen_at = st
    ns.entry_price = Decimal("100")
    ns.take_profit = Decimal("110")
    ns.stop_loss = Decimal("90")
    db.commit()
    db.close()

    h = timedelta(hours=1)

    def fake_load(_db, **kwargs):
        return [
            OhlcCandle(st.replace(minute=0), Decimal("100"), Decimal("105"), Decimal("99"), Decimal("101")),
            OhlcCandle(st.replace(minute=0) + h, Decimal("101"), Decimal("130"), Decimal("100"), Decimal("125")),
        ], "unit_test_candles"

    monkeypatch.setattr(
        "app.services.outcome_recalc_service.load_candles_for_window",
        fake_load,
    )

    lst = client.get(
        f"/api/v1/admin/signal-outcomes/?normalized_signal_id={ns_id}",
        headers=admin_headers,
    ).json()
    oid = next(x["id"] for x in lst if x["execution_model_key"] == "market_on_publish")
    r = client.post(
        f"/api/v1/admin/signal-outcomes/{oid}/recalculate",
        headers=admin_headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["outcome_status"] == "COMPLETE"
    assert body["sl_hit"] is False
    assert body["tp_hits"]
    assert body["entry_fill_price"] is not None


def test_stub_recalculate_sets_data_incomplete(client, admin_headers, ns_with_exec):
    ns_id = ns_with_exec
    client.post(f"/api/v1/admin/signal-outcomes/ensure/{ns_id}", headers=admin_headers)
    lst = client.get(
        f"/api/v1/admin/signal-outcomes/?normalized_signal_id={ns_id}",
        headers=admin_headers,
    )
    oid = lst.json()[0]["id"]
    r = client.post(
        f"/api/v1/admin/signal-outcomes/{oid}/stub-recalculate",
        headers=admin_headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["outcome_status"] == "DATA_INCOMPLETE"
    assert body["error_detail"]["code"] == "canonical_market_data_pipeline_not_enabled"


def test_stub_recalculate_rejects_complete(client, admin_headers, ns_with_exec):
    ns_id = ns_with_exec
    client.post(f"/api/v1/admin/signal-outcomes/ensure/{ns_id}", headers=admin_headers)
    oid = client.get(
        f"/api/v1/admin/signal-outcomes/?normalized_signal_id={ns_id}",
        headers=admin_headers,
    ).json()[0]["id"]
    client.patch(
        f"/api/v1/admin/signal-outcomes/{oid}",
        headers=admin_headers,
        json={"outcome_status": "COMPLETE"},
    )
    r = client.post(
        f"/api/v1/admin/signal-outcomes/{oid}/stub-recalculate",
        headers=admin_headers,
    )
    assert r.status_code == 422


def test_patch_outcome(client, admin_headers, ns_with_exec):
    ns_id = ns_with_exec
    client.post(f"/api/v1/admin/signal-outcomes/ensure/{ns_id}", headers=admin_headers)
    oid = client.get(
        f"/api/v1/admin/signal-outcomes/?normalized_signal_id={ns_id}",
        headers=admin_headers,
    ).json()[0]["id"]
    r = client.patch(
        f"/api/v1/admin/signal-outcomes/{oid}",
        headers=admin_headers,
        json={"outcome_status": "SKIPPED", "policy_ref": "manual#1"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["outcome_status"] == "SKIPPED"
    assert r.json()["policy_ref"] == "manual#1"


def test_patch_invalid_status_422(client, admin_headers, ns_with_exec):
    ns_id = ns_with_exec
    client.post(f"/api/v1/admin/signal-outcomes/ensure/{ns_id}", headers=admin_headers)
    oid = client.get(
        f"/api/v1/admin/signal-outcomes/?normalized_signal_id={ns_id}",
        headers=admin_headers,
    ).json()[0]["id"]
    r = client.patch(
        f"/api/v1/admin/signal-outcomes/{oid}",
        headers=admin_headers,
        json={"outcome_status": "NOT_A_STATUS"},
    )
    assert r.status_code == 422
