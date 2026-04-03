"""
Идемпотентность Stripe webhooks: event.id запоминается после успешной обработки.
Повторная доставка того же id → ответ duplicate без повторного изменения БД.
"""
from __future__ import annotations

import logging
from collections import OrderedDict
from typing import Optional

logger = logging.getLogger(__name__)

_MEMORY_MAX = 10_000
_processed_memory: OrderedDict[str, None] = OrderedDict()
_TTL_SEC = 7 * 24 * 3600


def _memory_remember(event_id: str) -> None:
    _processed_memory[event_id] = None
    _processed_memory.move_to_end(event_id)
    while len(_processed_memory) > _MEMORY_MAX:
        _processed_memory.popitem(last=False)


def _memory_seen(event_id: str) -> bool:
    return event_id in _processed_memory


def redis_seen(redis_url: str, event_id: str) -> Optional[bool]:
    """True — уже обработано; False — нет; None — Redis недоступен."""
    try:
        import redis as redis_lib

        r = redis_lib.from_url(redis_url, decode_responses=True)
        key = f"stripe:webhook:done:{event_id}"
        return bool(r.exists(key))
    except Exception as e:
        logger.debug("stripe webhook dedup redis seen: %s", e)
        return None


def redis_remember(redis_url: str, event_id: str) -> None:
    try:
        import redis as redis_lib

        r = redis_lib.from_url(redis_url, decode_responses=True)
        key = f"stripe:webhook:done:{event_id}"
        r.set(key, "1", ex=_TTL_SEC)
    except Exception as e:
        logger.debug("stripe webhook dedup redis remember: %s", e)


def stripe_event_already_processed(event_id: Optional[str], redis_url: str) -> bool:
    """True, если этот event.id уже успешно обработан ранее."""
    if not event_id or not str(event_id).strip():
        return False
    eid = str(event_id).strip()
    if redis_url:
        s = redis_seen(redis_url, eid)
        if s is not None:
            return s
    return _memory_seen(eid)


def mark_stripe_event_processed(event_id: Optional[str], redis_url: str) -> None:
    """Вызвать после успешного commit по событию."""
    if not event_id or not str(event_id).strip():
        return
    eid = str(event_id).strip()
    if redis_url:
        try:
            redis_remember(redis_url, eid)
        except Exception:
            pass
    _memory_remember(eid)


def clear_memory_dedup_for_tests() -> None:
    _processed_memory.clear()
