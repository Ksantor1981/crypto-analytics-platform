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


def test_channel_scrape_result_includes_posts_list():
    from app.services.telegram_scraper import ChannelPost, ChannelScrapeResult

    r = ChannelScrapeResult(posts_fetched=1, signals=[])
    assert r.posts == []
    p = ChannelPost(text="hi", message_id="99")
    r2 = ChannelScrapeResult(posts_fetched=1, signals=[], posts=[p])
    assert len(r2.posts) == 1


def test_persist_shadow_pipeline_skips_when_flag_off():
    from app.services.collection_pipeline import persist_shadow_telegram_posts_if_enabled
    from app.services.telegram_scraper import ChannelPost
    from unittest.mock import patch

    db = MagicMock()
    ch = MagicMock()
    ch.id = 1
    ch.owner_id = None
    posts = [ChannelPost(text="a", message_id="1")]
    with patch("app.core.config.get_settings") as gs:
        gs.return_value = MagicMock(SHADOW_PIPELINE_ENABLED=False)
        out = persist_shadow_telegram_posts_if_enabled(db, ch, posts, web_username="x")
    assert out == {"shadow_written": 0, "shadow_dedup": 0}
