"""Review Console admin API: queue, raw-event detail, RBAC."""
import uuid

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    import os

    os.environ["USE_SQLITE"] = "true"
    os.environ["SECRET_KEY"] = "test-secret-key-32-chars-minimum"
    os.environ["DEBUG"] = "true"
    # Сначала `import app.*`, иначе локальное имя `app` перезапишется пакетом и TestClient получит module.
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
    u = User(
        email=email,
        username=f"adm_{uuid.uuid4().hex[:6]}",
        hashed_password=get_password_hash("StrongPass123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.close()
    r = client.post("/api/v1/users/login", json={"email": email, "password": "StrongPass123!"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_headers(client):
    email = f"usr_{uuid.uuid4().hex[:8]}@example.com"
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
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestReviewQueue:
    def test_queue_requires_admin(self, client, user_headers):
        r = client.get("/api/v1/admin/review-labels/queue", headers=user_headers)
        assert r.status_code == 403

    def test_queue_admin_empty(self, client, admin_headers):
        # Общая SQLite БД и pytest-randomly: другие тесты оставляют raw_events без labels.
        from app.core.database import SessionLocal
        from app.models.extraction import Extraction
        from app.models.extraction_decision import ExtractionDecision
        from app.models.normalized_signal import NormalizedSignal
        from app.models.raw_ingestion import MessageVersion, RawEvent
        from app.models.review_label import ReviewLabel
        from app.models.signal_outcome import SignalOutcome
        from app.models.signal_relation import SignalRelation

        db = SessionLocal()
        try:
            db.query(SignalRelation).delete()
            db.query(SignalOutcome).delete()
            db.query(NormalizedSignal).delete()
            db.query(ExtractionDecision).delete()
            db.query(Extraction).delete()
            db.query(ReviewLabel).delete()
            db.query(MessageVersion).delete()
            db.query(RawEvent).delete()
            db.commit()
        finally:
            db.close()

        r = client.get("/api/v1/admin/review-labels/queue", headers=admin_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["items"] == []
        assert body["total"] == 0
        assert body["limit"] == 50
        assert body["offset"] == 0

    def test_raw_event_detail_404(self, client, admin_headers):
        r = client.get("/api/v1/admin/review-labels/raw-events/999999", headers=admin_headers)
        assert r.status_code == 404

    def test_raw_event_detail_includes_data_plane_snippets(self, client, admin_headers):
        from app.core.database import SessionLocal
        from app.models.execution_model import ExecutionModel
        from app.models.signal_outcome import SignalOutcome
        from test_normalized_signals_api import _insert_min_normalized_chain

        db = SessionLocal()
        db.query(SignalOutcome).delete()
        db.query(ExecutionModel).delete()
        db.commit()
        db.add(
            ExecutionModel(
                model_key="market_on_publish",
                display_name="MOP",
                description="t",
                fill_rule={},
                slippage_policy={},
                fee_policy={},
                expiry_policy={},
                is_active=True,
                sort_order=1,
            )
        )
        db.commit()
        db.close()

        raw_event_id, ns_id = _insert_min_normalized_chain()
        ens = client.post(
            f"/api/v1/admin/signal-outcomes/ensure/{ns_id}",
            headers=admin_headers,
        )
        assert ens.status_code == 200, ens.text

        r = client.get(
            f"/api/v1/admin/review-labels/raw-events/{raw_event_id}",
            headers=admin_headers,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert len(body["extractions"]) == 1
        assert body["extractions"][0]["decision"]["decision_type"] == "signal"
        assert len(body["normalized_signals"]) == 1
        assert body["normalized_signals"][0]["asset"] == "BTC"
        assert body["signal_relations"] == []
        assert len(body["signal_outcomes"]) == 1
        assert body["signal_outcomes"][0]["outcome_status"] == "PENDING"
        assert body["signal_outcomes"][0]["execution_model_key"] == "market_on_publish"

    def test_raw_event_detail_shows_take_profits_ladder(self, client, admin_headers):
        from sqlalchemy.orm.attributes import flag_modified

        from app.core.database import SessionLocal
        from app.models.normalized_signal import NormalizedSignal
        from test_normalized_signals_api import _insert_min_normalized_chain

        raw_event_id, ns_id = _insert_min_normalized_chain()
        db = SessionLocal()
        ns = db.query(NormalizedSignal).filter(NormalizedSignal.id == ns_id).first()
        assert ns is not None
        p = dict(ns.provenance or {})
        p["take_profits"] = [70000.0, 72000.0, 75000.0]
        ns.provenance = p
        flag_modified(ns, "provenance")
        db.commit()
        db.close()

        r = client.get(
            f"/api/v1/admin/review-labels/raw-events/{raw_event_id}",
            headers=admin_headers,
        )
        assert r.status_code == 200, r.text
        tps = r.json()["normalized_signals"][0].get("take_profits")
        assert tps == ["70000.0", "72000.0", "75000.0"]

    def test_raw_event_detail_take_profits_fallback_from_extraction(self, client, admin_headers):
        """Если в provenance нет цепочки — берём take_profits из extraction.extracted_fields."""
        from sqlalchemy.orm.attributes import flag_modified

        from app.core.database import SessionLocal
        from app.models.extraction import Extraction
        from app.models.normalized_signal import NormalizedSignal
        from test_normalized_signals_api import _insert_min_normalized_chain

        raw_event_id, ns_id = _insert_min_normalized_chain()
        db = SessionLocal()
        ns = db.query(NormalizedSignal).filter(NormalizedSignal.id == ns_id).first()
        assert ns is not None
        ns.provenance = {"extractor_name": "test", "extraction_id": int(ns.extraction_id)}
        flag_modified(ns, "provenance")
        ex = db.query(Extraction).filter(Extraction.id == ns.extraction_id).first()
        assert ex is not None
        ex.extracted_fields = {
            "asset": "BTC",
            "direction": "LONG",
            "entry_price": 1,
            "take_profits": [70000.0, 71000.0],
        }
        flag_modified(ex, "extracted_fields")
        db.commit()
        db.close()

        r = client.get(
            f"/api/v1/admin/review-labels/raw-events/{raw_event_id}",
            headers=admin_headers,
        )
        assert r.status_code == 200, r.text
        assert r.json()["normalized_signals"][0]["take_profits"] == ["70000.0", "71000.0"]

    def test_raw_event_detail_auto_ensures_outcomes_when_flag(
        self, client, admin_headers, monkeypatch
    ):
        """При OUTCOME_SLOTS_AUTO_ENSURE_ON_REVIEW_DETAIL слоты создаются без отдельного POST ensure."""
        from app.core.database import SessionLocal
        from app.models.execution_model import ExecutionModel
        from app.models.signal_outcome import SignalOutcome
        from test_normalized_signals_api import _insert_min_normalized_chain

        monkeypatch.setenv("OUTCOME_SLOTS_AUTO_ENSURE_ON_REVIEW_DETAIL", "true")

        db = SessionLocal()
        db.query(SignalOutcome).delete()
        db.query(ExecutionModel).delete()
        db.commit()
        db.add(
            ExecutionModel(
                model_key="market_on_publish",
                display_name="MOP",
                description="t",
                fill_rule={},
                slippage_policy={},
                fee_policy={},
                expiry_policy={},
                is_active=True,
                sort_order=1,
            )
        )
        db.commit()
        db.close()

        raw_event_id, _ns_id = _insert_min_normalized_chain()

        r = client.get(
            f"/api/v1/admin/review-labels/raw-events/{raw_event_id}",
            headers=admin_headers,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert len(body["signal_outcomes"]) == 1
        assert body["signal_outcomes"][0]["outcome_status"] == "PENDING"
