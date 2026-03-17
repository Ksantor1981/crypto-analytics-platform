"""
Celery tasks for automatic signal collection.
Can also be run standalone via: python -m app.tasks.collect_signals
"""
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from app.core.metrics import (
        SIGNALS_COLLECTED_RAW,
        SIGNALS_PARSED_OK,
        SIGNALS_SAVED,
        SIGNALS_SKIPPED,
    )
    _METRICS_AVAILABLE = True
except ImportError:
    _METRICS_AVAILABLE = False


def run_collection():
    """Run signal collection from all active Telegram channels. Works without Celery."""
    from app.core.config import get_settings
    from app.core.database import SessionLocal
    from app.models.channel import Channel
    from app.models.signal import Signal
    from app.services.telegram_scraper import collect_signals_from_channel
    from app.services.metrics_calculator import recalculate_all_channels

    logger.info(f"Starting signal collection at {datetime.utcnow().isoformat()}")

    db = SessionLocal()
    try:
        raw_posts_total = 0
        parsed_signals_total = 0
        skipped_no_entry_total = 0
        skipped_duplicates_total = 0

        channels = db.query(Channel).filter(
            Channel.is_active == True,
            Channel.platform == "telegram",
        ).all()

        total_saved = 0
        for channel in channels:
            username = channel.username
            if not username and channel.url:
                username = channel.url.rstrip("/").split("/")[-1]
            if not username:
                continue

            try:
                signals = asyncio.get_event_loop().run_until_complete(
                    collect_signals_from_channel(username)
                )
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                signals = loop.run_until_complete(
                    collect_signals_from_channel(username)
                )

            # Локальные счётчики по каналу
            raw_posts = len(signals)  # число ParsedSignal (постов, прошедших базовый парсинг)
            parsed_signals = 0
            skipped_no_entry = 0
            skipped_duplicates = 0

            from sqlalchemy import func
            new_count = 0
            text_500_col = func.left(Signal.original_text, 500)
            for sig in signals:
                if not sig.entry_price:
                    skipped_no_entry += 1
                    continue
                text_500 = (sig.original_text or "")[:500]
                existing = db.query(Signal).filter(
                    Signal.channel_id == channel.id,
                    text_500_col == text_500,
                ).first()
                if existing:
                    skipped_duplicates += 1
                    continue

                db_signal = Signal(
                    channel_id=channel.id,
                    asset=sig.asset,
                    symbol=sig.asset.replace("/", ""),
                    direction=sig.direction,
                    entry_price=sig.entry_price,
                    tp1_price=sig.take_profit,
                    stop_loss=sig.stop_loss,
                    confidence_score=sig.confidence,
                    original_text=sig.original_text,
                    status="PENDING",
                )
                db.add(db_signal)
                parsed_signals += 1
                new_count += 1

            if new_count > 0:
                channel.signals_count = (channel.signals_count or 0) + new_count
            total_saved += new_count

            raw_posts_total += raw_posts
            parsed_signals_total += parsed_signals
            skipped_no_entry_total += skipped_no_entry
            skipped_duplicates_total += skipped_duplicates

            if _METRICS_AVAILABLE:
                SIGNALS_COLLECTED_RAW.inc(raw_posts)
                SIGNALS_PARSED_OK.inc(parsed_signals)
                SIGNALS_SAVED.inc(new_count)
                SIGNALS_SKIPPED.labels(reason="no_entry_price").inc(skipped_no_entry)
                SIGNALS_SKIPPED.labels(reason="duplicate").inc(skipped_duplicates)

            logger.info(
                "Collection stats for channel %s: raw=%d, parsed_saved=%d, "
                "skipped_no_entry=%d, skipped_duplicates=%d",
                username,
                raw_posts,
                parsed_signals,
                skipped_no_entry,
                skipped_duplicates,
            )

        db.commit()
        recalculate_all_channels(db)
        logger.info(
            "Collection complete: %d channels, %d new signals "
            "(raw=%d, parsed_saved=%d, skipped_no_entry=%d, skipped_duplicates=%d)",
            len(channels),
            total_saved,
            raw_posts_total,
            parsed_signals_total,
            skipped_no_entry_total,
            skipped_duplicates_total,
        )
        return {
            "channels": len(channels),
            "new_signals": total_saved,
            "raw_posts": raw_posts_total,
            "parsed_signals_saved": parsed_signals_total,
            "skipped": {
                "no_entry_price": skipped_no_entry_total,
                "duplicates": skipped_duplicates_total,
            },
        }

    except Exception as e:
        logger.error(f"Collection error: {e}")
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_collection()
    print(f"Result: {result}")
