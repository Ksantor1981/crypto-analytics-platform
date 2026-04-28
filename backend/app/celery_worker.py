"""
Celery worker for background signal collection.
Run worker: celery -A app.celery_worker worker --loglevel=info
Run beat:   celery -A app.celery_worker beat --loglevel=info

Задачи: collect_all_signals, check_signal_outcomes, recalculate_canonical_signal_outcomes,
collect_telethon_all_channels (beat 04:15 UTC; включается CELERY_TELETHON_COLLECT_ENABLED + session Telethon на воркере).
"""
import os
import asyncio
import logging
from celery import Celery
from celery.schedules import crontab

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
# TTL lock ≥ ожидаемой длительности задачи; при падении воркера ключ истечёт сам
_COLLECT_LOCK_TTL = int(os.getenv("CELERY_COLLECT_LOCK_TTL", "1800"))
_CHECK_LOCK_TTL = int(os.getenv("CELERY_CHECK_SIGNALS_LOCK_TTL", "1700"))
_OUTCOME_RECALC_LOCK_TTL = int(os.getenv("CELERY_OUTCOME_RECALC_LOCK_TTL", "900"))
_TELETHON_COLLECT_LOCK_TTL = int(os.getenv("CELERY_TELETHON_COLLECT_LOCK_TTL", "7200"))

celery_app = Celery("crypto_analytics", broker=REDIS_URL, backend=REDIS_URL)

celery_app.conf.beat_schedule = {
    "collect-signals-every-15-min": {
        "task": "app.celery_worker.collect_all_signals",
        "schedule": 900,  # 15 minutes
    },
    "check-signals-every-30-min": {
        "task": "app.celery_worker.check_signal_outcomes",
        "schedule": 1800,  # 30 minutes
    },
    "recalculate-canonical-outcomes-hourly": {
        "task": "app.celery_worker.recalculate_canonical_signal_outcomes",
        "schedule": 3600,
    },
    # Telethon: раз в сутки UTC 04:15; задача сама выходит, если флаг выключен или нет session
    "collect-telethon-all-nightly-utc": {
        "task": "app.celery_worker.collect_telethon_all_channels",
        "schedule": crontab(hour=4, minute=15),
    },
}
celery_app.conf.timezone = "UTC"


@celery_app.task(name="app.celery_worker.collect_all_signals")
def collect_all_signals():
    """Celery task: collect signals from all Telegram channels."""
    if not os.getenv("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY must be set for Celery tasks (see env.example)")

    from app.core.redis_task_lock import celery_task_lock

    with celery_task_lock(REDIS_URL, "celery:lock:collect_all_signals", _COLLECT_LOCK_TTL) as acquired:
        if not acquired:
            return {"skipped": True, "reason": "lock_held"}

        from app.core.database import SessionLocal
        from app.core.config import get_settings
        from app.services.collection_pipeline import run_telegram_collection_cycle
        from app.services.metrics_calculator import recalculate_all_channels

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        db = SessionLocal()
        try:
            settings = get_settings()
            stats = loop.run_until_complete(run_telegram_collection_cycle(db, settings))
            total = stats.get("saved", 0)
            db.commit()
            recalculate_all_channels(db)
            logger.info(
                "Celery collected %s signals (channels=%s)",
                total,
                stats.get("channels"),
            )
            return {"channels": stats.get("channels", 0), "new_signals": total}
        except Exception as e:
            db.rollback()
            logger.error(f"Collection error: {e}")
            return {"error": str(e)}
        finally:
            db.close()
            loop.close()


@celery_app.task(name="app.celery_worker.collect_telethon_all_channels")
def collect_telethon_all_channels():
    """Celery: Telethon deep collect по всем активным Telegram-каналам (shadow + legacy)."""
    if not os.getenv("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY must be set for Celery tasks (see env.example)")

    from app.core.config import get_settings
    from app.services.telethon_collector import is_authenticated as telethon_ready

    settings = get_settings()
    if not settings.CELERY_TELETHON_COLLECT_ENABLED:
        return {"skipped": True, "reason": "CELERY_TELETHON_COLLECT_ENABLED=false"}
    if not telethon_ready():
        return {"skipped": True, "reason": "telethon_not_authenticated"}

    from app.core.redis_task_lock import celery_task_lock

    with celery_task_lock(
        REDIS_URL,
        "celery:lock:collect_telethon_all_channels",
        _TELETHON_COLLECT_LOCK_TTL,
    ) as acquired:
        if not acquired:
            return {"skipped": True, "reason": "lock_held"}

        from app.core.database import SessionLocal
        from app.services.collection_pipeline import run_telethon_collect_all_channels
        from app.services.metrics_calculator import recalculate_all_channels

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        db = SessionLocal()
        try:
            days = max(1, min(int(settings.TELETHON_COLLECT_DAYS_BACK), 365))
            batch = loop.run_until_complete(
                run_telethon_collect_all_channels(db, days),
            )
            db.commit()
            recalculate_all_channels(db)
            logger.info(
                "Celery Telethon collect-all: channels_processed=%s",
                batch.get("channels_processed"),
            )
            return batch
        except Exception as e:
            db.rollback()
            logger.error("Celery Telethon collect-all error: %s", e)
            return {"error": str(e)}
        finally:
            db.close()
            loop.close()


@celery_app.task(name="app.celery_worker.recalculate_canonical_signal_outcomes")
def recalculate_canonical_signal_outcomes():
    """Пересчёт PENDING signal_outcomes по свечам (канонический контур)."""
    if not os.getenv("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY must be set for Celery tasks (see env.example)")

    from app.core.redis_task_lock import celery_task_lock

    with celery_task_lock(
        REDIS_URL,
        "celery:lock:recalculate_canonical_signal_outcomes",
        _OUTCOME_RECALC_LOCK_TTL,
    ) as acquired:
        if not acquired:
            return {"skipped": True, "reason": "lock_held"}

        from app.core.config import get_settings
        from app.core.database import SessionLocal
        from app.services.outcome_recalc_service import process_pending_signal_outcomes

        settings = get_settings()
        if not settings.OUTCOME_RECALC_ENABLED:
            return {"skipped": True, "reason": "OUTCOME_RECALC_ENABLED=false"}

        db = SessionLocal()
        try:
            stats = process_pending_signal_outcomes(
                db,
                limit=settings.OUTCOME_RECALC_BATCH_LIMIT,
                lookahead_days=settings.OUTCOME_RECALC_LOOKAHEAD_DAYS,
                timeframe=settings.OUTCOME_RECALC_TIMEFRAME,
            )
            logger.info(
                "Canonical outcome recalc: processed=%s ok=%s failed=%s",
                stats.get("processed"),
                stats.get("ok"),
                stats.get("failed"),
            )
            return stats
        except Exception as e:
            logger.error("Canonical outcome recalc error: %s", e)
            return {"error": str(e)}
        finally:
            db.close()


@celery_app.task(name="app.celery_worker.check_signal_outcomes")
def check_signal_outcomes():
    """Celery task: check pending signals against market prices."""
    if not os.getenv("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY must be set for Celery tasks (see env.example)")

    from app.core.redis_task_lock import celery_task_lock

    with celery_task_lock(REDIS_URL, "celery:lock:check_signal_outcomes", _CHECK_LOCK_TTL) as acquired:
        if not acquired:
            return {"skipped": True, "reason": "lock_held"}

        from app.core.database import SessionLocal
        from app.services.signal_checker import check_pending_signals

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        db = SessionLocal()
        try:
            result = loop.run_until_complete(check_pending_signals(db))
            logger.info(f"Celery checked signals: {result.get('updated', 0)} updated")
            return result
        except Exception as e:
            logger.error(f"Signal check error: {e}")
            return {"error": str(e)}
        finally:
            db.close()
            loop.close()
