"""
Celery tasks for automatic signal collection.
Can also be run standalone via: python -m app.tasks.collect_signals
"""
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def run_collection():
    """Сбор Telegram + опционально Reddit через единый pipeline (дедуп, fingerprint, метрики)."""
    from app.core.config import get_settings
    from app.core.database import SessionLocal
    from app.services.collection_pipeline import run_full_collection_async
    from app.services.metrics_calculator import recalculate_all_channels

    logger.info("Starting signal collection at %s", datetime.utcnow().isoformat())

    db = SessionLocal()
    settings = get_settings()

    try:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("closed")
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(run_full_collection_async(db, settings))
        db.commit()
        recalculate_all_channels(db)

        tg = result.get("telegram") or {}
        rd = result.get("reddit") or {}
        total_saved = tg.get("saved", 0) + rd.get("saved", 0)

        logger.info(
            "Collection complete: tg_channels=%s tg_saved=%s reddit_saved=%s "
            "tg_skips=%s details=%s",
            tg.get("channels"),
            tg.get("saved"),
            rd.get("saved"),
            {
                "telegram": {k: tg.get(k) for k in ("skipped_no_entry", "skipped_duplicate", "posts_fetched")},
                "reddit": {k: rd.get(k) for k in ("skipped_no_entry", "skipped_duplicate")},
            },
            result,
        )
        return {
            "telegram": tg,
            "reddit": rd,
            "new_signals": total_saved,
            # обратная совместимость: число обработанных TG-каналов
            "channels": tg.get("channels", 0),
        }

    except Exception as e:
        logger.error("Collection error: %s", e)
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_collection()
    print(f"Result: {result}")
