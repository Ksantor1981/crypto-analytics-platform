"""
Распределённый lock для Celery (SET NX + освобождение по токену).
При недоступности Redis задача всё равно выполняется (fallback для single-node / dev).
"""
from __future__ import annotations

import logging
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


@contextmanager
def celery_task_lock(redis_url: str, lock_key: str, ttl_sec: int) -> Iterator[bool]:
    """
    True — lock взят, выполнять работу.
    False — lock уже у другого воркера, пропуск.
    При пустом redis_url или ошибке подключения — True (как раньше).
    """
    url = (redis_url or "").strip()
    if not url:
        yield True
        return

    r = None
    token = str(uuid.uuid4())
    try:
        import redis as redis_lib

        r = redis_lib.from_url(url, decode_responses=True, socket_connect_timeout=3)
        acquired = r.set(lock_key, token, nx=True, ex=max(30, int(ttl_sec)))
    except Exception as e:
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
