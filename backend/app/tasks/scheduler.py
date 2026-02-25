"""
Background scheduler for periodic signal collection.
Uses asyncio instead of Celery for simplicity.
"""
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

COLLECTION_INTERVAL = 900  # 15 minutes


async def periodic_collection():
    """Run signal collection every 15 minutes."""
    from app.core.database import SessionLocal
    from app.models.channel import Channel
    from app.models.signal import Signal
    from app.services.telegram_scraper import collect_signals_from_channel
    from app.services.metrics_calculator import recalculate_all_channels
    from app.services.signal_checker import check_pending_signals

    while True:
        await asyncio.sleep(COLLECTION_INTERVAL)
        logger.info(f"[Scheduler] Starting periodic collection at {datetime.utcnow().isoformat()}")

        db = SessionLocal()
        try:
            channels = db.query(Channel).filter(
                Channel.is_active == True, Channel.platform == "telegram"
            ).all()

            total = 0
            for ch in channels:
                uname = ch.username or (ch.url or "").rstrip("/").split("/")[-1]
                if not uname:
                    continue
                try:
                    sigs = await collect_signals_from_channel(uname)
                    for s in sigs:
                        if not s.entry_price:
                            continue
                        if db.query(Signal).filter(
                            Signal.channel_id == ch.id,
                            Signal.original_text == s.original_text[:500]
                        ).first():
                            continue
                        db.add(Signal(
                            channel_id=ch.id, asset=s.asset,
                            symbol=s.asset.replace("/", ""),
                            direction=s.direction, entry_price=s.entry_price,
                            tp1_price=s.take_profit, stop_loss=s.stop_loss,
                            confidence_score=s.confidence,
                            original_text=s.original_text, status="PENDING",
                        ))
                        total += 1
                        ch.signals_count = (ch.signals_count or 0) + 1
                except Exception as e:
                    logger.warning(f"[Scheduler] @{uname}: {e}")

            db.commit()

            # Check pending signals against market
            result = await check_pending_signals(db)
            recalculate_all_channels(db)

            logger.info(
                f"[Scheduler] Done: {total} new signals, "
                f"{result.get('updated', 0)} signals checked"
            )
        except Exception as e:
            logger.error(f"[Scheduler] Error: {e}")
            db.rollback()
        finally:
            db.close()
