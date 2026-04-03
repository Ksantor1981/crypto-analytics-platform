"""Доп. покрытие: dedup.signal_exists (legacy), stripe_webhook_dedup."""
from unittest.mock import MagicMock, patch

from app.services import dedup


def test_normalize_text_for_dedup_empty_and_whitespace():
    assert dedup.normalize_text_for_dedup(None) == ""
    assert dedup.normalize_text_for_dedup("") == ""
    assert dedup.normalize_text_for_dedup("  A  \n  B  ") == "a b"


def test_signal_exists_legacy_prefix_match():
    fq = MagicMock()
    fq.first.return_value = None
    m1 = MagicMock()
    m1.filter.return_value = fq

    leg = MagicMock()
    leg.original_text = "Hello legacy signal text"
    leg.content_fingerprint = None
    sq = MagicMock()
    sq.all.return_value = [leg]
    m2 = MagicMock()
    m2.filter.return_value = sq

    db = MagicMock()
    db.query.side_effect = [m1, m2]

    assert dedup.signal_exists(db, 7, "Hello legacy signal text") is True


def test_signal_exists_empty_text_no_legacy_query():
    fq = MagicMock()
    fq.first.return_value = None
    m1 = MagicMock()
    m1.filter.return_value = fq
    db = MagicMock()
    db.query.return_value = m1

    assert dedup.signal_exists(db, 1, "") is False
    assert db.query.call_count == 1


def test_stripe_dedup_redis_short_circuit():
    from app.core import stripe_webhook_dedup as swd

    swd.clear_memory_dedup_for_tests()
    with patch.object(swd, "redis_seen", return_value=True):
        assert swd.stripe_event_already_processed("evt_1", "redis://localhost/0") is True
    with patch.object(swd, "redis_seen", return_value=False):
        assert swd.stripe_event_already_processed("evt_2", "redis://localhost/0") is False


def test_stripe_redis_seen_handles_client_errors():
    from app.core import stripe_webhook_dedup as swd

    with patch("redis.from_url", side_effect=RuntimeError("down")):
        assert swd.redis_seen("redis://x", "id") is None


def test_stripe_redis_remember_swallows_client_errors():
    from app.core import stripe_webhook_dedup as swd

    with patch("redis.from_url", side_effect=ConnectionError("bad")):
        swd.redis_remember("redis://x", "evt_x")


def test_stripe_memory_remember_evicts_oldest():
    from app.core import stripe_webhook_dedup as swd

    swd.clear_memory_dedup_for_tests()
    with patch.object(swd, "_MEMORY_MAX", 3):
        for i in range(4):
            swd._memory_remember(f"k{i}")
    assert "k0" not in swd._processed_memory
    assert "k3" in swd._processed_memory
