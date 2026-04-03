"""Shadow raw ingestion: флаг и сервис без записи в БД при выключенном pipeline."""
from unittest.mock import MagicMock, patch

from app.models.raw_ingestion import MessageVersion, RawEvent


def test_shadow_disabled_no_db_write():
    from app.services.raw_ingestion_service import persist_raw_event_from_payload

    db = MagicMock()
    with patch("app.services.raw_ingestion_service.get_settings") as gs:
        gs.return_value = MagicMock(SHADOW_PIPELINE_ENABLED=False)
        out = persist_raw_event_from_payload(
            db,
            source_type="telegram",
            raw_payload={"x": 1},
        )
    assert out is None
    db.add.assert_not_called()


def test_raw_ingestion_models_tablenames():
    assert RawEvent.__tablename__ == "raw_events"
    assert MessageVersion.__tablename__ == "message_versions"
