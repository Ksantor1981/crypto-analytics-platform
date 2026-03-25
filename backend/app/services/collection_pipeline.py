"""
Единая логика сохранения распарсенных сигналов (Telegram / Reddit) + лимиты постов.
Используется в collect_signals, scheduler, Celery, main auto-collect, API collect.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.channel import Channel
from app.models.signal import Signal
from app.services.dedup import content_fingerprint, signal_exists

if TYPE_CHECKING:
    from app.services.telegram_scraper import ParsedSignal

logger = logging.getLogger(__name__)

try:
    from app.core.metrics import (
        SIGNALS_COLLECTED_RAW,
        SIGNALS_PARSED_OK,
        SIGNALS_POSTS_FETCHED,
        SIGNALS_SAVED,
        SIGNALS_SKIPPED,
    )

    _METRICS = True
except ImportError:
    _METRICS = False


def telegram_fetch_limit(channel: Channel, settings: Any) -> int:
    """Лимит постов: base + (priority-1)*step, не выше max."""
    base = getattr(settings, "TELEGRAM_POSTS_BASE_LIMIT", 20)
    step = getattr(settings, "TELEGRAM_POSTS_PRIORITY_STEP", 5)
    max_lim = getattr(settings, "TELEGRAM_POSTS_MAX_LIMIT", 80)
    pr = channel.priority or 1
    return min(max_lim, base + max(0, int(pr) - 1) * step)


def persist_parsed_signals_for_channel(
    db: Session,
    channel: Channel,
    signals: List["ParsedSignal"],
    *,
    posts_fetched: int = 0,
    record_metrics: bool = True,
    use_message_time_for_created_at: bool = False,
) -> Dict[str, int]:
    """
    Сохраняет ParsedSignal в БД с дедупом по content_fingerprint.

    Returns:
        saved, skipped_no_entry, skipped_duplicate, parsed_with_entry (кол-во сигналов с ценой входа)
    """
    saved = 0
    skipped_no_entry = 0
    skipped_duplicate = 0
    parsed_with_entry = 0

    for sig in signals:
        if not sig.entry_price:
            skipped_no_entry += 1
            continue
        parsed_with_entry += 1

        if signal_exists(db, channel.id, sig.original_text):
            skipped_duplicate += 1
            continue

        fp = content_fingerprint(sig.original_text)
        db_signal = Signal(
            channel_id=channel.id,
            asset=sig.asset,
            symbol=sig.asset.replace("/", ""),
            direction=sig.direction,
            entry_price=Decimal(str(sig.entry_price)),
            tp1_price=Decimal(str(sig.take_profit)) if sig.take_profit is not None else None,
            stop_loss=Decimal(str(sig.stop_loss)) if sig.stop_loss is not None else None,
            confidence_score=sig.confidence,
            original_text=sig.original_text,
            content_fingerprint=fp,
            status="PENDING",
            message_timestamp=sig.timestamp,
            timestamp=sig.timestamp,
            telegram_message_id=sig.telegram_message_id,
        )
        if getattr(sig, "entry_zone_low", None) is not None:
            db_signal.entry_price_low = Decimal(str(sig.entry_zone_low))
        if getattr(sig, "entry_zone_high", None) is not None:
            db_signal.entry_price_high = Decimal(str(sig.entry_zone_high))

        db.add(db_signal)
        if use_message_time_for_created_at and getattr(sig, "timestamp", None) is not None:
            ts = sig.timestamp
            db_signal.created_at = ts
            db_signal.updated_at = ts
        saved += 1

    if saved > 0:
        channel.signals_count = (channel.signals_count or 0) + saved

    if record_metrics and _METRICS:
        if posts_fetched:
            SIGNALS_POSTS_FETCHED.inc(posts_fetched)
        # «сырые» прошедшие парсер текста (ParsedSignal объекты)
        SIGNALS_COLLECTED_RAW.inc(len(signals))
        SIGNALS_PARSED_OK.inc(parsed_with_entry)
        SIGNALS_SAVED.inc(saved)
        SIGNALS_SKIPPED.labels(reason="no_entry_price").inc(skipped_no_entry)
        SIGNALS_SKIPPED.labels(reason="duplicate").inc(skipped_duplicate)

    try:
        from app.core.config import get_settings as _gs

        _log_funnel = _gs().COLLECT_LOG_PARSE_FUNNEL
    except Exception:
        _log_funnel = True
    if _log_funnel:
        logger.info(
            "parse_funnel channel_id=%s platform=%s posts_fetched=%s parsed=%s "
            "saved=%s skip_no_entry=%s skip_dup=%s",
            channel.id,
            getattr(channel, "platform", "?"),
            posts_fetched,
            len(signals),
            saved,
            skipped_no_entry,
            skipped_duplicate,
        )

    return {
        "saved": saved,
        "skipped_no_entry": skipped_no_entry,
        "skipped_duplicate": skipped_duplicate,
        "parsed_with_entry": parsed_with_entry,
    }


def aggregate_stats(total: Dict[str, int], part: Dict[str, int]) -> None:
    for k in ("saved", "skipped_no_entry", "skipped_duplicate", "parsed_with_entry"):
        total[k] = total.get(k, 0) + part.get(k, 0)


async def run_telegram_collection_cycle(db: Session, settings: Any) -> Dict[str, Any]:
    """Один цикл сбора по всем активным Telegram-каналам (без commit/recalculate)."""
    from app.services.telegram_scraper import collect_signals_from_channel

    channels = (
        db.query(Channel)
        .filter(Channel.is_active == True, Channel.platform == "telegram")
        .all()
        if settings.COLLECT_TELEGRAM
        else []
    )

    total: Dict[str, int] = {}
    raw_posts = 0

    for channel in channels:
        uname = channel.username or (channel.url or "").rstrip("/").split("/")[-1]
        if not uname:
            continue
        lim = telegram_fetch_limit(channel, settings)
        try:
            result = await collect_signals_from_channel(uname, limit=lim)
        except Exception as e:
            logger.warning("Telegram collect @%s: %s", uname, e)
            continue

        raw_posts += result.posts_fetched
        st = persist_parsed_signals_for_channel(
            db,
            channel,
            result.signals,
            posts_fetched=result.posts_fetched,
            record_metrics=True,
        )
        aggregate_stats(total, st)

    total["posts_fetched"] = raw_posts
    total["channels"] = len(channels)
    return total


async def run_reddit_collection_cycle(db: Session, settings: Any) -> Dict[str, Any]:
    """Один цикл Reddit (как в scheduler): каналы r_<sub>, дедуп через pipeline."""
    from app.services.reddit_scraper import collect_reddit_signals, CRYPTO_SUBREDDITS

    total: Dict[str, int] = {}
    for sub in CRYPTO_SUBREDDITS:
        try:
            res = await collect_reddit_signals(sub, limit=25)
            channel = db.query(Channel).filter(Channel.username == f"r_{sub}").first()
            if not channel:
                channel = Channel(
                    username=f"r_{sub}",
                    name=f"r/{sub}",
                    url=f"https://reddit.com/r/{sub}",
                    platform="reddit",
                    description=f"Reddit r/{sub}",
                    category="community",
                    is_active=True,
                    status="active",
                    signals_count=0,
                )
                db.add(channel)
                db.flush()

            st = persist_parsed_signals_for_channel(
                db,
                channel,
                res.signals,
                posts_fetched=res.posts_fetched,
                record_metrics=True,
            )
            aggregate_stats(total, st)
        except Exception as e:
            logger.warning("Reddit r/%s: %s", sub, e)

    total["subreddits"] = len(CRYPTO_SUBREDDITS)
    return total


async def run_full_collection_async(db: Session, settings: Any) -> Dict[str, Any]:
    """Telegram + опционально Reddit в одной сессии (перед commit вызывающий делает commit)."""
    out: Dict[str, Any] = {"telegram": {}, "reddit": {}}
    out["telegram"] = await run_telegram_collection_cycle(db, settings)
    if getattr(settings, "COLLECT_REDDIT_IN_RUN_COLLECTION", True):
        out["reddit"] = await run_reddit_collection_cycle(db, settings)
    return out
