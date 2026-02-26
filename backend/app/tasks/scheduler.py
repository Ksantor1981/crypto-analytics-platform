"""
Background scheduler for periodic signal collection.
Uses asyncio instead of Celery for simplicity.
"""
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

COLLECTION_INTERVAL = 900  # 15 minutes
REDDIT_INTERVAL = 1800  # 30 minutes


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


async def periodic_reddit_collection():
    """Collect signals from Reddit every 30 minutes."""
    from app.core.database import SessionLocal
    from app.models.channel import Channel
    from app.models.signal import Signal
    from app.services.reddit_scraper import collect_reddit_signals, CRYPTO_SUBREDDITS

    while True:
        await asyncio.sleep(REDDIT_INTERVAL)
        logger.info("[Scheduler] Reddit collection starting...")

        db = SessionLocal()
        try:
            total = 0
            for sub in CRYPTO_SUBREDDITS:
                try:
                    sigs = await collect_reddit_signals(sub, limit=25)
                    for sig in sigs:
                        if not sig.entry_price:
                            continue
                        channel = db.query(Channel).filter(Channel.username == f"r_{sub}").first()
                        if not channel:
                            channel = Channel(
                                username=f"r_{sub}", name=f"r/{sub}",
                                url=f"https://reddit.com/r/{sub}", platform="reddit",
                                description=f"Reddit r/{sub}", category="community",
                                is_active=True, status="active", signals_count=0,
                            )
                            db.add(channel)
                            db.flush()
                        if db.query(Signal).filter(Signal.channel_id == channel.id, Signal.original_text == sig.original_text[:500]).first():
                            continue
                        db.add(Signal(
                            channel_id=channel.id, asset=sig.asset, symbol=sig.asset.replace("/", ""),
                            direction=sig.direction, entry_price=sig.entry_price,
                            tp1_price=sig.take_profit, stop_loss=sig.stop_loss,
                            confidence_score=sig.confidence, original_text=sig.original_text,
                            status="PENDING", message_timestamp=sig.timestamp,
                        ))
                        total += 1
                        channel.signals_count = (channel.signals_count or 0) + 1
                except Exception as e:
                    logger.warning(f"[Scheduler] Reddit r/{sub}: {e}")
            db.commit()
            logger.info(f"[Scheduler] Reddit: {total} new signals from {len(CRYPTO_SUBREDDITS)} subs")
        except Exception as e:
            logger.error(f"[Scheduler] Reddit error: {e}")
            db.rollback()
        finally:
            db.close()
