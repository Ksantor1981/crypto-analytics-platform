"""Redis lock для Celery — без живого Redis (mock)."""
from unittest.mock import MagicMock, patch

import pytest


def test_celery_task_lock_empty_url_always_acquired():
    from app.core.redis_task_lock import celery_task_lock

    with celery_task_lock("", "celery:lock:test", 60) as acquired:
        assert acquired is True


def test_celery_task_lock_skip_when_key_held():
    from app.core.redis_task_lock import celery_task_lock

    fake = MagicMock()
    fake.set.return_value = None
    with patch("redis.from_url", return_value=fake):
        with celery_task_lock("redis://localhost:6379/0", "celery:lock:x", 120) as acquired:
            assert acquired is False


def test_celery_task_lock_acquire_release():
    from app.core.redis_task_lock import celery_task_lock

    fake = MagicMock()
    fake.set.return_value = True
    with patch("redis.from_url", return_value=fake):
        with celery_task_lock("redis://localhost:6379/0", "celery:lock:y", 120) as acquired:
            assert acquired is True
            fake.set.assert_called_once()
        fake.eval.assert_called_once()


def test_celery_task_lock_redis_error_falls_back_to_run(monkeypatch):
    """В dev (`CELERY_LOCK_HARD_FAIL` не задан, `ENVIRONMENT=development`) — мягкий fallback."""
    monkeypatch.delenv("CELERY_LOCK_HARD_FAIL", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "development")
    from app.core.redis_task_lock import celery_task_lock

    with patch("redis.from_url", side_effect=OSError("no redis")):
        with celery_task_lock("redis://bad", "celery:lock:z", 60) as acquired:
            assert acquired is True


def test_celery_task_lock_hard_fail_raises_when_redis_down(monkeypatch):
    """F5: `CELERY_LOCK_HARD_FAIL=true` → недоступный Redis = `CeleryLockUnavailable`."""
    monkeypatch.setenv("CELERY_LOCK_HARD_FAIL", "true")
    from app.core.redis_task_lock import celery_task_lock, CeleryLockUnavailable

    with patch("redis.from_url", side_effect=OSError("no redis")):
        with pytest.raises(CeleryLockUnavailable):
            with celery_task_lock("redis://bad", "celery:lock:hf", 60):
                pass


def test_celery_task_lock_hard_fail_raises_on_empty_url(monkeypatch):
    """F5: пустой `redis_url` под hard-fail тоже отказывает."""
    monkeypatch.setenv("CELERY_LOCK_HARD_FAIL", "true")
    from app.core.redis_task_lock import celery_task_lock, CeleryLockUnavailable

    with pytest.raises(CeleryLockUnavailable):
        with celery_task_lock("", "celery:lock:empty", 60):
            pass


def test_celery_task_lock_production_defaults_to_hard_fail(monkeypatch):
    """F5: в production (без явного флага) hard-fail включён."""
    monkeypatch.delenv("CELERY_LOCK_HARD_FAIL", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "production")
    from app.core.redis_task_lock import celery_task_lock, CeleryLockUnavailable

    with pytest.raises(CeleryLockUnavailable):
        with celery_task_lock("", "celery:lock:prod", 60):
            pass
