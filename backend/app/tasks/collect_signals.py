"""
Celery tasks for automatic signal collection.
Can also be run standalone via: python -m app.tasks.collect_signals
"""
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


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

            from sqlalchemy import func
            new_count = 0
            text_500_col = func.left(Signal.original_text, 500)
            for sig in signals:
                if not sig.entry_price:
                    continue
                text_500 = (sig.original_text or "")[:500]
                existing = db.query(Signal).filter(
                    Signal.channel_id == channel.id,
                    text_500_col == text_500,
                ).first()
                if existing:
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
                new_count += 1

            if new_count > 0:
                channel.signals_count = (channel.signals_count or 0) + new_count
            total_saved += new_count

        db.commit()
        recalculate_all_channels(db)
        logger.info(f"Collection complete: {len(channels)} channels, {total_saved} new signals")
        return {"channels": len(channels), "new_signals": total_saved}

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
