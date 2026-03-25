"""
Celery worker for background signal collection.
Run: celery -A app.celery_worker worker --beat --loglevel=info
"""
import os
import asyncio
import logging
from celery import Celery
from celery.schedules import crontab

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

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
}
celery_app.conf.timezone = "UTC"


@celery_app.task(name="app.celery_worker.collect_all_signals")
def collect_all_signals():
    """Celery task: collect signals from all Telegram channels."""
    os.environ.setdefault("USE_SQLITE", "true")
    os.environ.setdefault("SECRET_KEY", "celery-worker-key-32-chars-min!")

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


@celery_app.task(name="app.celery_worker.check_signal_outcomes")
def check_signal_outcomes():
    """Celery task: check pending signals against market prices."""
    os.environ.setdefault("USE_SQLITE", "true")
    os.environ.setdefault("SECRET_KEY", "celery-worker-key-32-chars-min!")

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
