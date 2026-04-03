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


def test_persist_shadow_reddit_skips_when_flag_off():
    from app.services.collection_pipeline import persist_shadow_reddit_posts_if_enabled
    from unittest.mock import patch

    db = MagicMock()
    ch = MagicMock()
    ch.id = 1
    ch.owner_id = None
    posts = [{"title": "x", "text": "y", "created": None, "url": "https://reddit.com/a"}]
    with patch("app.core.config.get_settings") as gs:
        gs.return_value = MagicMock(SHADOW_PIPELINE_ENABLED=False)
        out = persist_shadow_reddit_posts_if_enabled(db, ch, posts, subreddit="test", scrape_mode="rss")
    assert out == {"shadow_written": 0, "shadow_versioned": 0, "shadow_dedup": 0}


def test_upsert_shadow_created_when_no_existing_row():
    from app.services.raw_ingestion_service import upsert_shadow_raw_event

    with patch("app.services.raw_ingestion_service.get_settings") as gs:
        gs.return_value = MagicMock(SHADOW_PIPELINE_ENABLED=True)
        db = MagicMock()
        raw_q = MagicMock()
        raw_q.filter.return_value.one_or_none.return_value = None
        db.query.return_value = raw_q
        fake_ev = MagicMock()
        with patch(
            "app.services.raw_ingestion_service._insert_raw_event_and_initial_version",
            return_value=fake_ev,
        ) as ins:
            ev, action = upsert_shadow_raw_event(
                db,
                source_type="telegram_web",
                raw_payload={"a": 1},
                channel_id=1,
                platform_message_id="42",
                raw_text="x",
            )
        assert action == "created"
        assert ev is fake_ev
        ins.assert_called_once()


def test_upsert_shadow_unchanged_when_same_text():
    from app.services.raw_ingestion_service import upsert_shadow_raw_event

    with patch("app.services.raw_ingestion_service.get_settings") as gs:
        gs.return_value = MagicMock(SHADOW_PIPELINE_ENABLED=True)
        db = MagicMock()
        existing = MagicMock()
        existing.id = 10
        raw_q = MagicMock()
        raw_q.filter.return_value.one_or_none.return_value = existing
        latest = MagicMock()
        latest.version_no = 1
        latest.text_snapshot = "hello"
        latest.content_hash = "hh"
        mv_q = MagicMock()
        mv_q.filter.return_value.order_by.return_value.first.return_value = latest

        def _query(model):
            if model is RawEvent:
                return raw_q
            if model is MessageVersion:
                return mv_q
            return MagicMock()

        db.query.side_effect = _query
        ev, action = upsert_shadow_raw_event(
            db,
            source_type="telegram_web",
            raw_payload={"k": 2},
            channel_id=1,
            platform_message_id="42",
            raw_text="hello",
        )
        assert action == "unchanged"
        assert ev is existing
        db.add.assert_not_called()


def test_upsert_shadow_versioned_when_text_changes():
    from app.services.raw_ingestion_service import upsert_shadow_raw_event

    with patch("app.services.raw_ingestion_service.get_settings") as gs:
        gs.return_value = MagicMock(SHADOW_PIPELINE_ENABLED=True)
        db = MagicMock()
        existing = MagicMock()
        existing.id = 10
        raw_q = MagicMock()
        raw_q.filter.return_value.one_or_none.return_value = existing
        latest = MagicMock()
        latest.version_no = 1
        latest.text_snapshot = "hello"
        latest.content_hash = "hh"
        mv_q = MagicMock()
        mv_q.filter.return_value.order_by.return_value.first.return_value = latest

        def _query(model):
            if model is RawEvent:
                return raw_q
            if model is MessageVersion:
                return mv_q
            return MagicMock()

        db.query.side_effect = _query
        ev, action = upsert_shadow_raw_event(
            db,
            source_type="telegram_web",
            raw_payload={"k": 2},
            channel_id=1,
            platform_message_id="42",
            raw_text="hello edited",
        )
        assert action == "versioned"
        assert ev is existing
        db.add.assert_called_once()
        added = db.add.call_args[0][0]
        assert isinstance(added, MessageVersion)
        assert added.version_no == 2
        assert added.version_reason == "rescanned"


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
    assert out == {"shadow_written": 0, "shadow_versioned": 0, "shadow_dedup": 0}


def test_persist_shadow_telegram_includes_mtproto_in_payload():
    from contextlib import nullcontext

    from app.services.collection_pipeline import persist_shadow_telegram_posts_if_enabled
    from app.services.telegram_scraper import ChannelPost

    seen = []

    def capture_upsert(_db, **kwargs):
        seen.append(kwargs.get("raw_payload") or {})
        ev = MagicMock()
        return ev, "created"

    db = MagicMock()
    db.begin_nested = lambda: nullcontext()
    ch = MagicMock()
    ch.id = 1
    ch.owner_id = None
    mt = {"_": "Message", "id": 99}
    posts = [ChannelPost(text="hi", message_id="10", mtproto=mt)]
    with patch("app.core.config.get_settings") as gs:
        gs.return_value = MagicMock(SHADOW_PIPELINE_ENABLED=True)
        with patch(
            "app.services.raw_ingestion_service.upsert_shadow_raw_event",
            side_effect=capture_upsert,
        ):
            out = persist_shadow_telegram_posts_if_enabled(
                db, ch, posts, web_username="chan", payload_scraper="telethon"
            )
    assert out["shadow_written"] == 1
    assert seen[0].get("mtproto") == mt
    assert seen[0].get("scraper") == "telethon"
