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


def test_celery_task_lock_redis_error_falls_back_to_run():
    from app.core.redis_task_lock import celery_task_lock

    with patch("redis.from_url", side_effect=OSError("no redis")):
        with celery_task_lock("redis://bad", "celery:lock:z", 60) as acquired:
            assert acquired is True
