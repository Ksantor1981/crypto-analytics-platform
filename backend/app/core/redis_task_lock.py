"""
Распределённый lock для Celery (SET NX + освобождение по токену).

Поведение при недоступном Redis регулируется флагом `CELERY_LOCK_HARD_FAIL`:
- production / соответствующий флаг: поднимаем `CeleryLockUnavailable` →
  задача падает наглядно вместо тихого «прошло без lock» (исключаем дубликаты).
- dev / single-node: мягкий fallback (yield True), исторически совместимое поведение.
"""
from __future__ import annotations

import logging
import os
import uuid
from contextlib import contextmanager
from typing import Iterator

logger = logging.getLogger(__name__)

_RELEASE_LUA = """
if redis.call("get", KEYS[1]) == ARGV[1] then
  return redis.call("del", KEYS[1])
end
return 0
"""


class CeleryLockUnavailable(RuntimeError):
    """Поднимается, когда Redis недоступен и `CELERY_LOCK_HARD_FAIL=true`."""


def _hard_fail_enabled() -> bool:
    """Жёсткий режим по умолчанию в production."""
    flag = os.getenv("CELERY_LOCK_HARD_FAIL")
    if flag is not None:
        return flag.strip().lower() in ("1", "true", "yes", "on")
    env = (os.getenv("ENVIRONMENT", "development") or "development").lower()
    return env == "production"


@contextmanager
def celery_task_lock(redis_url: str, lock_key: str, ttl_sec: int) -> Iterator[bool]:
    """
    True — lock взят, выполнять работу.
    False — lock уже у другого воркера, пропуск.

    Если `CELERY_LOCK_HARD_FAIL=true` (либо `ENVIRONMENT=production` без явного
    переопределения), пустой/недоступный Redis приводит к `CeleryLockUnavailable`,
    а не к тихому выполнению без lock.
    """
    url = (redis_url or "").strip()
    hard_fail = _hard_fail_enabled()

    if not url:
        if hard_fail:
            raise CeleryLockUnavailable(
                f"celery_task_lock: redis_url is empty for key={lock_key}"
            )
        yield True
        return

    r = None
    token = str(uuid.uuid4())
    try:
        import redis as redis_lib

        r = redis_lib.from_url(url, decode_responses=True, socket_connect_timeout=3)
        acquired = r.set(lock_key, token, nx=True, ex=max(30, int(ttl_sec)))
    except Exception as e:
        if hard_fail:
            logger.error("celery_task_lock: redis unavailable for key=%s: %s", lock_key, e)
            raise CeleryLockUnavailable(
                f"celery_task_lock: redis unavailable for key={lock_key}: {e}"
            ) from e
        logger.warning("celery_task_lock: redis unavailable (%s), run without lock", e)
        yield True
        return

    if not acquired:
        logger.info("celery_task_lock: skip %s (already running)", lock_key)
        yield False
        return

    try:
        yield True
    finally:
        try:
            r.eval(_RELEASE_LUA, 1, lock_key, token)
        except Exception as e:
            logger.debug("celery_task_lock: release %s: %s", lock_key, e)
