"""Admin normalized-signals API."""
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
            username=f"n_{uuid.uuid4().hex[:6]}",
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


def test_materialize_pipeline_off_503(client, admin_headers):
    r = client.post(
        "/api/v1/admin/normalized-signals/materialize/1",
        headers=admin_headers,
    )
    assert r.status_code == 503


def test_materialize_requires_admin(client, user_headers):
    from unittest.mock import MagicMock, patch

    with patch(
        "app.api.endpoints.normalized_signals.get_settings",
        return_value=MagicMock(EXTRACTION_PIPELINE_ENABLED=True),
    ):
        r = client.post(
            "/api/v1/admin/normalized-signals/materialize/1",
            headers=user_headers,
        )
    assert r.status_code == 403


def test_materialize_unknown_extraction_404(client, admin_headers):
    from unittest.mock import MagicMock, patch

    with patch(
        "app.api.endpoints.normalized_signals.get_settings",
        return_value=MagicMock(EXTRACTION_PIPELINE_ENABLED=True),
    ):
        r = client.post(
            "/api/v1/admin/normalized-signals/materialize/999999",
            headers=admin_headers,
        )
    assert r.status_code == 404


def test_list_requires_admin(client, user_headers):
    r = client.get("/api/v1/admin/normalized-signals/?raw_event_id=1", headers=user_headers)
    assert r.status_code == 403


def test_list_admin_empty(client, admin_headers):
    # id, не совпадающий с фикстурами других тестов (общий SQLite-файл)
    r = client.get(
        "/api/v1/admin/normalized-signals/?raw_event_id=999999999",
        headers=admin_headers,
    )
    assert r.status_code == 200
    assert r.json() == []


def test_patch_legacy_normalized_not_found(client, admin_headers):
    r = client.patch(
        "/api/v1/admin/normalized-signals/999999/legacy-link",
        headers=admin_headers,
        json={"legacy_signal_id": 1},
    )
    assert r.status_code == 404


def test_patch_legacy_requires_admin(client, user_headers):
    r = client.patch(
        "/api/v1/admin/normalized-signals/1/legacy-link",
        headers=user_headers,
        json={"legacy_signal_id": None},
    )
    assert r.status_code == 403


def _insert_min_normalized_chain():
    """RawEvent → MessageVersion → Extraction → NormalizedSignal (SQLite tests)."""
    from sqlalchemy import func

    from app.core.database import SessionLocal
    from app.models.extraction import Extraction
    from app.models.extraction_decision import ExtractionDecision
    from app.models.normalized_signal import NormalizedSignal
    from app.models.raw_ingestion import MessageVersion, RawEvent
    from app.models.review_label import ReviewLabel

    def _next_id(db, model):
        m = db.query(func.max(model.id)).scalar()
        return int(m or 0) + 1

    rid = uuid.uuid4().hex[:16]
    db = SessionLocal()
    re_id = _next_id(db, RawEvent)
    ev = RawEvent(
        id=re_id,
        source_type="tg",
        raw_payload={},
        platform_message_id=rid,
        raw_text="ping",
    )
    db.add(ev)
    db.flush()
    mv_id = _next_id(db, MessageVersion)
    mv = MessageVersion(
        id=mv_id,
        raw_event_id=ev.id,
        version_no=1,
        text_snapshot="ping",
        version_reason="initial",
    )
    db.add(mv)
    db.flush()
    ex_id = _next_id(db, Extraction)
    ex = Extraction(
        id=ex_id,
        raw_event_id=ev.id,
        message_version_id=mv.id,
        extractor_name="test",
        extractor_version="1",
        classification_status="PARSED",
        extracted_fields={},
    )
    db.add(ex)
    db.flush()
    dec_id = _next_id(db, ExtractionDecision)
    db.add(
        ExtractionDecision(
            id=dec_id,
            extraction_id=ex.id,
            raw_event_id=ev.id,
            decision_type="signal",
            decision_source="rules_v0",
            confidence=0.9,
        )
    )
    db.flush()
    ns_row_id = _next_id(db, NormalizedSignal)
    ns = NormalizedSignal(
        id=ns_row_id,
        raw_event_id=ev.id,
        message_version_id=mv.id,
        extraction_id=ex.id,
        asset="BTC",
        direction="LONG",
        entry_price=1,
        trading_lifecycle_status="PENDING_ENTRY",
        relation_status="UNLINKED",
    )
    db.add(ns)
    db.add(
        ReviewLabel(
            raw_event_id=ev.id,
            reviewer_name="fixture",
            label_type="commentary",
        )
    )
    db.commit()
    raw_event_id = int(ev.id)
    ns_id = int(ns.id)
    db.close()
    return raw_event_id, ns_id


def _insert_extraction_only_chain():
    """RawEvent → MessageVersion → Extraction + Decision без NormalizedSignal (для materialize)."""
    from sqlalchemy import func

    from app.core.database import SessionLocal
    from app.models.extraction import Extraction
    from app.models.extraction_decision import ExtractionDecision
    from app.models.raw_ingestion import MessageVersion, RawEvent

    def _next_id(db, model):
        m = db.query(func.max(model.id)).scalar()
        return int(m or 0) + 1

    rid = uuid.uuid4().hex[:16]
    db = SessionLocal()
    re_id = _next_id(db, RawEvent)
    ev = RawEvent(
        id=re_id,
        source_type="tg",
        raw_payload={},
        platform_message_id=rid,
        raw_text="ping",
    )
    db.add(ev)
    db.flush()
    mv_id = _next_id(db, MessageVersion)
    mv = MessageVersion(
        id=mv_id,
        raw_event_id=ev.id,
        version_no=1,
        text_snapshot="ping",
        version_reason="initial",
    )
    db.add(mv)
    db.flush()
    ex_id = _next_id(db, Extraction)
    ex = Extraction(
        id=ex_id,
        raw_event_id=ev.id,
        message_version_id=mv.id,
        extractor_name="test",
        extractor_version="1",
        classification_status="PARSED",
        extracted_fields={
            "asset": "BTC",
            "direction": "LONG",
            "entry_price": 65000.0,
            "take_profit": 70000.0,
            "take_profits": [70000.0, 72000.0, 75000.0],
        },
    )
    db.add(ex)
    db.flush()
    dec_id = _next_id(db, ExtractionDecision)
    db.add(
        ExtractionDecision(
            id=dec_id,
            extraction_id=ex.id,
            raw_event_id=ev.id,
            decision_type="signal",
            decision_source="rules_v0",
            confidence=0.9,
        )
    )
    db.commit()
    ex_id_int = int(ex.id)
    db.close()
    return ex_id_int


def test_patch_lifecycle_active_ok(client, admin_headers):
    _, ns_id = _insert_min_normalized_chain()
    r = client.patch(
        f"/api/v1/admin/normalized-signals/{ns_id}/lifecycle",
        headers=admin_headers,
        json={"trading_lifecycle_status": "ACTIVE"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["trading_lifecycle_status"] == "ACTIVE"


def test_patch_lifecycle_invalid_transition_422(client, admin_headers):
    _, ns_id = _insert_min_normalized_chain()
    r = client.patch(
        f"/api/v1/admin/normalized-signals/{ns_id}/lifecycle",
        headers=admin_headers,
        json={"trading_lifecycle_status": "COMPLETED_TP"},
    )
    assert r.status_code == 422


def test_patch_lifecycle_not_found_404(client, admin_headers):
    r = client.patch(
        "/api/v1/admin/normalized-signals/999999/lifecycle",
        headers=admin_headers,
        json={"trading_lifecycle_status": "ACTIVE"},
    )
    assert r.status_code == 404


def test_patch_lifecycle_requires_admin(client, user_headers):
    r = client.patch(
        "/api/v1/admin/normalized-signals/1/lifecycle",
        headers=user_headers,
        json={"trading_lifecycle_status": "ACTIVE"},
    )
    assert r.status_code == 403


def test_patch_lifecycle_case_insensitive_target(client, admin_headers):
    _, ns_id = _insert_min_normalized_chain()
    r = client.patch(
        f"/api/v1/admin/normalized-signals/{ns_id}/lifecycle",
        headers=admin_headers,
        json={"trading_lifecycle_status": "active"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["trading_lifecycle_status"] == "ACTIVE"


def test_materialize_sets_take_profits_in_provenance(client, admin_headers, monkeypatch):
    monkeypatch.setenv("EXTRACTION_PIPELINE_ENABLED", "true")
    monkeypatch.setenv("OUTCOME_SLOTS_AUTO_ENSURE", "false")
    ex_id = _insert_extraction_only_chain()
    r = client.post(
        f"/api/v1/admin/normalized-signals/materialize/{ex_id}",
        headers=admin_headers,
    )
    assert r.status_code == 200, r.text
    prov = r.json().get("provenance") or {}
    assert prov.get("take_profits") == [70000.0, 72000.0, 75000.0]
