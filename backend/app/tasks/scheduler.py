"""
Background scheduler for periodic signal collection.
Uses asyncio instead of Celery for simplicity.
"""
import asyncio
import logging
import os
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

def _env_int(name: str, default: int) -> int:
    try:
        return max(30, int(os.environ.get(name, str(default))))
    except ValueError:
        return default


# Интервалы сбора (сек). Docker: COLLECTION_INTERVAL_SECONDS=120 для плотного опроса
COLLECTION_INTERVAL = _env_int("COLLECTION_INTERVAL_SECONDS", 300)
REDDIT_INTERVAL = _env_int(
    "REDDIT_COLLECTION_INTERVAL_SECONDS",
    COLLECTION_INTERVAL,
)
WEEKLY_DIGEST_INTERVAL = 604800  # 7 days
DAILY_REVALIDATION_INTERVAL = 86400  # 24 hours
ML_TRAIN_INTERVAL = 86400  # 24 hours — переобучение ML раз в сутки
SOURCE_HEALTH_INTERVAL = 86400  # 24 hours — регулярная проверка источников
SOURCE_DISCOVERY_INTERVAL = 86400  # 24 hours — auto-add/cleanup источников


async def periodic_collection():
    """Run signal collection every 15 minutes. C1: if COLLECT_TELEGRAM=false, skip Telegram (Reddit runs separately)."""
    from app.core.database import SessionLocal
    from app.core.config import get_settings
    from app.services.collection_pipeline import run_telegram_collection_cycle
    from app.services.metrics_calculator import recalculate_all_channels
    from app.services.signal_checker import check_pending_signals
    from app.services.dedup import cleanup_duplicates

    collection_cycle = 0
    while True:
        await asyncio.sleep(COLLECTION_INTERVAL)
        collection_cycle += 1
        logger.info(f"[Scheduler] Starting periodic collection at {datetime.utcnow().isoformat()}")

        db = SessionLocal()
        try:
            settings = get_settings()
            stats = await run_telegram_collection_cycle(db, settings)
            total = stats.get("saved", 0)

            db.commit()

            # Периодическая очистка дубликатов по полному тексту (раз в ~1 час при интервале 5 мин)
            if collection_cycle % 12 == 0:
                try:
                    removed = cleanup_duplicates(db)
                    if removed:
                        logger.info(f"[Scheduler] cleanup_duplicates removed {removed} duplicates")
                except Exception as e:
                    logger.warning(f"[Scheduler] cleanup_duplicates: {e}")

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
    from app.core.config import get_settings
    from app.services.reddit_scraper import CRYPTO_SUBREDDITS
    from app.services.collection_pipeline import run_reddit_collection_cycle

    while True:
        await asyncio.sleep(REDDIT_INTERVAL)
        logger.info("[Scheduler] Reddit collection starting...")

        db = SessionLocal()
        try:
            settings = get_settings()
            stats = await run_reddit_collection_cycle(db, settings)
            total = stats.get("saved", 0)
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


async def periodic_ml_train():
    """Run ML model training once per day (train_from_db.py in ml-service)."""
    while True:
        await asyncio.sleep(ML_TRAIN_INTERVAL)
        logger.info("[Scheduler] ML training starting...")

        try:
            from app.core.config import get_settings
            settings = get_settings()
            # Path to ml-service (sibling of backend)
            backend_dir = Path(__file__).resolve().parents[2]
            project_root = backend_dir.parent
            ml_service_dir = project_root / "ml-service"
            train_script = ml_service_dir / "train_from_db.py"
            if not train_script.exists():
                logger.warning("[Scheduler] ml-service/train_from_db.py not found, skip ML train")
                continue
            from app.core.config import database_url_for_host
            env = os.environ.copy()
            env["DATABASE_URL"] = database_url_for_host(settings.database_url)
            proc = await asyncio.create_subprocess_exec(
                os.environ.get("PYTHON_EXE", "python"),
                str(train_script),
                cwd=str(ml_service_dir),
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0:
                logger.info("[Scheduler] ML training finished successfully")
            else:
                logger.warning("[Scheduler] ML training exit code %s: %s", proc.returncode, (stderr or stdout).decode()[:500])
        except Exception as e:
            logger.error("[Scheduler] ML training error: %s", e)


async def periodic_source_health():
    """
    Regular health check for all data sources (channels).

    Считаем, сколько сигналов пришло за последнюю неделю по каждому каналу,
    и логируем агрегированную статистику, чтобы видеть «живость» источников.
    """
    from datetime import datetime, timedelta
    from app.core.database import SessionLocal
    from app.models.channel import Channel
    from app.models.signal import Signal

    while True:
        await asyncio.sleep(SOURCE_HEALTH_INTERVAL)
        logger.info("[Scheduler] Source health check starting...")

        db = SessionLocal()
        try:
            now = datetime.utcnow()
            week_ago = now - timedelta(days=7)

            total_channels = 0
            active_channels = 0
            zero_signals = 0

            for ch in db.query(Channel).all():
                total_channels += 1
                recent_count = (
                    db.query(Signal)
                    .filter(Signal.channel_id == ch.id, Signal.created_at >= week_ago)
                    .count()
                )
                if recent_count > 0:
                    active_channels += 1
                else:
                    zero_signals += 1

            logger.info(
                "[Scheduler] Source health: total_channels=%d, active_last_7d=%d, zero_last_7d=%d",
                total_channels,
                active_channels,
                zero_signals,
            )
        except Exception as e:
            logger.error("[Scheduler] Source health error: %s", e)
        finally:
            db.close()


async def periodic_source_discovery():
    """
    Auto-add new sources and auto-clean stale sources.

    - Reddit: discover new subreddits via public search RSS and add them as channels.
    - Telegram: best-effort discovery via public directory search pages (no TG API keys).
    - Cleanup: auto-deactivate channels that stopped producing signals.
    """
    from app.core.database import SessionLocal
    from app.services.source_discovery import (
        discover_reddit_sources,
        discover_telegram_sources_tgstat,
        upsert_sources,
        deactivate_stale_sources,
    )

    reddit_queries = [
        "LONG entry TP SL",
        "SHORT entry TP SL",
        "BTCUSDT LONG entry",
        "ETHUSDT SHORT entry",
        "signal entry take profit stop loss",
    ]
    tg_keywords = [
        "crypto signals",
        "binance signals",
        "BTC signals",
        "altcoin signals",
        "futures signals",
    ]

    while True:
        await asyncio.sleep(SOURCE_DISCOVERY_INTERVAL)
        logger.info("[Scheduler] Source discovery starting...")

        db = SessionLocal()
        try:
            reddit_sources = await discover_reddit_sources(reddit_queries)
            tg_sources = await discover_telegram_sources_tgstat(tg_keywords)
            stats_upsert = upsert_sources(db, [*reddit_sources, *tg_sources])
            stats_cleanup = deactivate_stale_sources(db, days_without_signals=14)
            db.commit()
            logger.info(
                "[Scheduler] Source discovery done: added=%d updated=%d deactivated=%d",
                stats_upsert["added"],
                stats_upsert["updated"],
                stats_cleanup["deactivated"],
            )
        except Exception as e:
            logger.error("[Scheduler] Source discovery error: %s", e)
            db.rollback()
        finally:
            db.close()
