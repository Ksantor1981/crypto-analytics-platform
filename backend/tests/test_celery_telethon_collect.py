"""Celery task collect_telethon_all_channels: флаги и early skip."""
from unittest.mock import MagicMock, patch


def test_collect_telethon_task_skips_when_disabled():
    from app.celery_worker import collect_telethon_all_channels

    with patch(
        "app.core.config.get_settings",
        return_value=MagicMock(
            CELERY_TELETHON_COLLECT_ENABLED=False,
            TELETHON_COLLECT_DAYS_BACK=7,
        ),
    ):
        r = collect_telethon_all_channels()
    assert r.get("skipped") is True
    assert "false" in (r.get("reason") or "").lower()


def test_collect_telethon_task_skips_when_not_authenticated():
    from app.celery_worker import collect_telethon_all_channels

    with patch(
        "app.core.config.get_settings",
        return_value=MagicMock(
            CELERY_TELETHON_COLLECT_ENABLED=True,
            TELETHON_COLLECT_DAYS_BACK=7,
        ),
    ):
        with patch(
            "app.services.telethon_collector.is_authenticated",
            return_value=False,
        ):
            r = collect_telethon_all_channels()
    assert r.get("skipped") is True
    assert "telethon" in (r.get("reason") or "").lower()
