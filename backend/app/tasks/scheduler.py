"""
Background scheduler for periodic signal collection.
Uses asyncio instead of Celery for simplicity.
"""
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

COLLECTION_INTERVAL = 300  # 5 minutes (ROADMAP: было 15 мин)
REDDIT_INTERVAL = 300  # 5 minutes (ROADMAP: было 30 мин)
WEEKLY_DIGEST_INTERVAL = 604800  # 7 days
DAILY_REVALIDATION_INTERVAL = 86400  # 24 hours


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


async def periodic_weekly_digest():
    """Send weekly digest email to all active users."""
    from app.core.database import SessionLocal
    from app.models.user import User
    from app.models.signal import Signal
    from app.models.channel import Channel
    from datetime import datetime, timedelta
    from app.services.email_service import EmailService

    while True:
        await asyncio.sleep(WEEKLY_DIGEST_INTERVAL)
        logger.info("[Scheduler] Weekly digest starting...")

        db = SessionLocal()
        try:
            week_ago = datetime.utcnow() - timedelta(days=7)
            signals_count = db.query(Signal).filter(Signal.created_at >= week_ago).count()
            top_signals = (
                db.query(Signal)
                .filter(Signal.created_at >= week_ago)
                .order_by(Signal.confidence_score.desc().nullslast())
                .limit(10)
                .all()
            )
            top_channels = (
                db.query(Channel)
                .filter(Channel.is_active == True)
                .order_by(Channel.signals_count.desc().nullslast())
                .limit(10)
                .all()
            )
            top_signals_data = [
                {"asset": s.asset, "direction": s.direction, "confidence": s.confidence_score}
                for s in top_signals
            ]
            top_channels_data = [
                {"name": c.name or c.username, "signals_count": c.signals_count or 0}
                for c in top_channels
            ]

            users = db.query(User).filter(User.is_active == True).all()
            svc = EmailService()
            sent = 0
            for u in users:
                if u.email:
                    ok = await svc.send_weekly_digest(u, signals_count, top_signals_data, top_channels_data)
                    if ok:
                        sent += 1
            logger.info(f"[Scheduler] Weekly digest sent to {sent}/{len(users)} users")
        except Exception as e:
            logger.error(f"[Scheduler] Weekly digest error: {e}")
        finally:
            db.close()


async def periodic_daily_revalidation():
    """Daily revalidation of PENDING signals against current market prices."""
    from app.core.database import SessionLocal
    from app.models.signal import Signal
    from app.services.price_validator import validate_signal_price

    while True:
        await asyncio.sleep(DAILY_REVALIDATION_INTERVAL)
        logger.info("[Scheduler] Daily price revalidation starting...")

        db = SessionLocal()
        try:
            pending = db.query(Signal).filter(Signal.status == "PENDING").all()
            expired = 0
            for sig in pending:
                if not sig.entry_price:
                    continue
                try:
                    result = await validate_signal_price(sig.asset, float(sig.entry_price))
                    if not result.get("valid") and "deviation" in str(result.get("reason", "")):
                        sig.status = "EXPIRED"
                        expired += 1
                except Exception as e:
                    logger.warning(f"[Scheduler] Revalidation skip {sig.id}: {e}")
            if expired > 0:
                db.commit()
            logger.info(f"[Scheduler] Daily revalidation: {expired} signals expired")
        except Exception as e:
            logger.error(f"[Scheduler] Daily revalidation error: {e}")
            db.rollback()
        finally:
            db.close()
