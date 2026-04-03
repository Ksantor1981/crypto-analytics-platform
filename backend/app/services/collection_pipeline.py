"""
Единая логика сохранения распарсенных сигналов (Telegram / Reddit) + лимиты постов.
Используется в collect_signals, scheduler, Celery, main auto-collect, API collect.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import os
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.channel import Channel
from app.models.signal import Signal, TelegramSignal
from app.services.dedup import content_fingerprint, signal_exists

if TYPE_CHECKING:
    from app.services.telegram_scraper import ChannelPost, ParsedSignal

logger = logging.getLogger(__name__)


def _fire_custom_alerts_for_new_signals(signals_batch: List[Signal], db: Session) -> None:
    """Pro custom alerts: вне активного event loop (типичный sync collect) — asyncio.run."""
    if not signals_batch:
        return
    try:
        asyncio.get_running_loop()
        return
    except RuntimeError:
        pass
    try:
        from app.services.custom_alerts_service import custom_alerts_service
    except ImportError:
        return
    for s in signals_batch:
        try:
            asyncio.run(custom_alerts_service.trigger_alert_check(s, db))
        except Exception as e:
            logger.debug("custom_alerts hook skipped: %s", e)


try:
    from app.core.metrics import (
        SIGNALS_COLLECTED_RAW,
        SIGNALS_PARSED_OK,
        SIGNALS_POSTS_FETCHED,
        SIGNALS_SAVED,
        SIGNALS_SKIPPED,
        SHADOW_RAW_EVENTS_WRITTEN,
        SHADOW_RAW_EVENTS_DEDUP,
        SHADOW_MESSAGE_VERSIONS_ADDED,
    )

    _METRICS = True
except ImportError:
    _METRICS = False
    SHADOW_RAW_EVENTS_WRITTEN = None  # type: ignore[assignment,misc]
    SHADOW_RAW_EVENTS_DEDUP = None  # type: ignore[assignment,misc]
    SHADOW_MESSAGE_VERSIONS_ADDED = None  # type: ignore[assignment,misc]


def persist_shadow_telegram_posts_if_enabled(
    db: Session,
    channel: Channel,
    posts: List["ChannelPost"],
    *,
    web_username: str,
    source_type: str = "telegram_web",
    payload_scraper: str = "telegram_web_tme_s",
) -> Dict[str, int]:
    """
    Фаза 3 data plane: dual-write постов (t.me/s или Telethon) в raw_events + message_versions.
    Повтор с тем же текстом → dedup; смена текста → новая MessageVersion (versioned).
    """
    from app.core.config import get_settings
    from app.services.raw_ingestion_service import upsert_shadow_raw_event

    if not get_settings().SHADOW_PIPELINE_ENABLED or not posts:
        return {"shadow_written": 0, "shadow_versioned": 0, "shadow_dedup": 0}

    written = 0
    versioned = 0
    dedup = 0
    owner_id = getattr(channel, "owner_id", None)

    for post in posts:
        payload: Dict[str, Any] = {
            "scraper": payload_scraper,
            "channel_username": web_username,
            "telegram_message_id": post.message_id,
            "views": post.views,
            "image_urls": list(post.image_urls) if post.image_urls else [],
            "post_date": post.date.isoformat() if post.date else None,
        }
        pmid = str(post.message_id) if post.message_id else None
        with db.begin_nested():
            _ev, action = upsert_shadow_raw_event(
                db,
                source_type=source_type,
                raw_payload=payload,
                channel_id=channel.id,
                author_id=owner_id,
                platform_message_id=pmid,
                raw_text=post.text or None,
                media_refs=list(post.image_urls) if post.image_urls else None,
                source_observed_at=post.date,
            )
            if action == "created":
                written += 1
            elif action == "versioned":
                versioned += 1
                if _METRICS and SHADOW_MESSAGE_VERSIONS_ADDED is not None:
                    SHADOW_MESSAGE_VERSIONS_ADDED.inc()
            elif action == "unchanged":
                dedup += 1
                if _METRICS and SHADOW_RAW_EVENTS_DEDUP is not None:
                    SHADOW_RAW_EVENTS_DEDUP.inc()

    if written and _METRICS and SHADOW_RAW_EVENTS_WRITTEN is not None:
        SHADOW_RAW_EVENTS_WRITTEN.inc(written)

    if written or dedup or versioned:
        logger.info(
            "shadow_raw channel_id=%s username=%s written=%s versioned=%s dedup=%s",
            channel.id,
            web_username,
            written,
            versioned,
            dedup,
        )

    return {
        "shadow_written": written,
        "shadow_versioned": versioned,
        "shadow_dedup": dedup,
    }


def _reddit_platform_message_id(post: Dict[str, Any]) -> str:
    fn = (post.get("reddit_fullname") or "").strip()
    if fn:
        return fn[:128]
    u = (post.get("url") or "").strip()
    if u:
        return u[:128]
    key = f"{post.get('title', '')}|{post.get('created')}"
    return hashlib.sha256(key.encode("utf-8", errors="replace")).hexdigest()[:64]


def persist_shadow_reddit_posts_if_enabled(
    db: Session,
    channel: Channel,
    posts: List[Dict[str, Any]],
    *,
    subreddit: str,
    scrape_mode: str = "rss",
) -> Dict[str, int]:
    """
    Dual-write постов Reddit (RSS или JSON window) в raw_events.
    """
    from app.core.config import get_settings
    from app.services.raw_ingestion_service import upsert_shadow_raw_event

    if not get_settings().SHADOW_PIPELINE_ENABLED or not posts:
        return {"shadow_written": 0, "shadow_versioned": 0, "shadow_dedup": 0}

    written = 0
    versioned = 0
    dedup = 0
    owner_id = getattr(channel, "owner_id", None)

    for post in posts:
        payload: Dict[str, Any] = {
            "scraper": f"reddit_{scrape_mode}",
            "subreddit": subreddit,
            "title": post.get("title"),
            "url": post.get("url"),
            "reddit_fullname": post.get("reddit_fullname"),
            "permalink": post.get("permalink"),
            "author": post.get("author"),
            "link": post.get("link"),
        }
        pmid = _reddit_platform_message_id(post)
        raw_txt = (post.get("text") or "").strip()
        if not raw_txt:
            raw_txt = f"{post.get('title', '')}\n{post.get('body', '')}".strip()

        with db.begin_nested():
            _ev, action = upsert_shadow_raw_event(
                db,
                source_type=f"reddit_{scrape_mode}",
                raw_payload=payload,
                channel_id=channel.id,
                author_id=owner_id,
                platform_message_id=pmid or None,
                raw_text=raw_txt or None,
                source_observed_at=post.get("created"),
            )
            if action == "created":
                written += 1
            elif action == "versioned":
                versioned += 1
                if _METRICS and SHADOW_MESSAGE_VERSIONS_ADDED is not None:
                    SHADOW_MESSAGE_VERSIONS_ADDED.inc()
            elif action == "unchanged":
                dedup += 1
                if _METRICS and SHADOW_RAW_EVENTS_DEDUP is not None:
                    SHADOW_RAW_EVENTS_DEDUP.inc()

    if written and _METRICS and SHADOW_RAW_EVENTS_WRITTEN is not None:
        SHADOW_RAW_EVENTS_WRITTEN.inc(written)

    if written or dedup or versioned:
        logger.info(
            "shadow_raw_reddit channel_id=%s sub=%s mode=%s written=%s versioned=%s dedup=%s",
            channel.id,
            subreddit,
            scrape_mode,
            written,
            versioned,
            dedup,
        )

    return {
        "shadow_written": written,
        "shadow_versioned": versioned,
        "shadow_dedup": dedup,
    }


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
        saved, raw_saved, skipped_no_entry, skipped_duplicate, raw_skipped_duplicate,
        parsed_with_entry (кол-во сигналов с ценой входа)
    """
    saved = 0
    raw_saved = 0
    skipped_no_entry = 0
    skipped_duplicate = 0
    raw_skipped_duplicate = 0
    parsed_with_entry = 0
    new_signals_batch: List[Signal] = []

    store_raw = str(getattr(channel, "platform", "")).lower() == "telegram" and (
        os.getenv("STORE_RAW_TELEGRAM_SIGNALS", "true").lower() in ("1", "true", "yes")
    )

    for sig in signals:
        if not sig.entry_price:
            if not store_raw:
                skipped_no_entry += 1
                continue

            # RAW telegram signal: keep asset+direction+text+media evidence, even without entry/TP/SL.
            # Dedup by (source + original_text) to avoid unbounded growth.
            source = getattr(channel, "username", None) or getattr(channel, "name", "telegram")
            exists = (
                db.query(TelegramSignal)
                .filter(TelegramSignal.source == source, TelegramSignal.original_text == sig.original_text)
                .first()
            )
            if exists:
                raw_skipped_duplicate += 1
                continue

            fp = content_fingerprint(sig.original_text)
            meta: Dict[str, Any] = {
                "kind": "RAW_MEDIA_SIGNAL",
                "fingerprint": fp,
                "telegram_message_id": getattr(sig, "telegram_message_id", None),
                "timestamp": sig.timestamp.isoformat() if getattr(sig, "timestamp", None) else None,
            }
            db_raw = TelegramSignal(
                symbol=str(sig.asset or "").replace("/", "").upper()[:20] or "UNKNOWN",
                signal_type=str(getattr(sig, "direction", "")).lower() or "unknown",
                entry_price=None,
                target_price=None,
                stop_loss=None,
                confidence=getattr(sig, "confidence", 0.5),
                source=source,
                original_text=sig.original_text,
                signal_metadata=meta,
                status="PENDING",
            )
            db.add(db_raw)
            raw_saved += 1
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
        new_signals_batch.append(db_signal)
        if use_message_time_for_created_at and getattr(sig, "timestamp", None) is not None:
            ts = sig.timestamp
            db_signal.created_at = ts
            db_signal.updated_at = ts
        saved += 1

    if new_signals_batch:
        try:
            db.flush()
        except Exception as e:
            logger.warning("flush before custom_alerts hook: %s", e)
        _fire_custom_alerts_for_new_signals(new_signals_batch, db)

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
            "saved=%s raw_saved=%s skip_no_entry=%s skip_dup=%s raw_skip_dup=%s",
            channel.id,
            getattr(channel, "platform", "?"),
            posts_fetched,
            len(signals),
            saved,
            raw_saved,
            skipped_no_entry,
            skipped_duplicate,
            raw_skipped_duplicate,
        )

    return {
        "saved": saved,
        "raw_saved": raw_saved,
        "skipped_no_entry": skipped_no_entry,
        "skipped_duplicate": skipped_duplicate,
        "raw_skipped_duplicate": raw_skipped_duplicate,
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
        persist_shadow_telegram_posts_if_enabled(db, channel, result.posts, web_username=uname)
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

            persist_shadow_reddit_posts_if_enabled(
                db, channel, res.reddit_posts, subreddit=sub, scrape_mode="rss"
            )
            st = persist_parsed_signals_for_channel(
                db,
                channel,
                res.signals,
                posts_fetched=res.posts_fetched,
                record_metrics=True,
            )
            aggregate_stats(total, st)
        except Exception as e:
            # Keep the rest of subreddits processing even if one item fails.
            # Without rollback SQLAlchemy session stays in aborted transaction state
            # and every next DB call fails with InFailedSqlTransaction.
            try:
                db.rollback()
            except Exception:
                pass
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
