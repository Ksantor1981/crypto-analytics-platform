"""
Дозаполнение сигналов за интервал дат [start, end), когда обычный сбор не писал в БД.

Telegram: пагинация t.me/s (deep_collector.fetch_all_posts), фильтр по дате поста.
Reddit: /r/sub/new.json с пагинацией (RSS не даёт глубину по времени).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models.channel import Channel
from app.services.collection_pipeline import persist_parsed_signals_for_channel, aggregate_stats
from app.services.deep_collector import fetch_all_posts
from app.services.reddit_scraper import CRYPTO_SUBREDDITS, collect_reddit_signals_in_window
from app.services.telegram_scraper import parse_signal_from_text, ParsedSignal

logger = logging.getLogger(__name__)


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


async def backfill_telegram_window(
    db: Session,
    settings: Any,
    start: datetime,
    end: datetime,
    *,
    max_pages: int = 45,
) -> Dict[str, Any]:
    """Собрать сигналы из активных Telegram-каналов за [start, end)."""
    start = _ensure_utc(start)
    end = _ensure_utc(end)

    if not getattr(settings, "COLLECT_TELEGRAM", True):
        return {"skipped": True, "reason": "COLLECT_TELEGRAM=false"}

    channels = (
        db.query(Channel)
        .filter(Channel.is_active == True, Channel.platform == "telegram")
        .all()
    )

    total: Dict[str, int] = {}
    raw_posts = 0

    for channel in channels:
        uname = channel.username or (channel.url or "").rstrip("/").split("/")[-1]
        if not uname:
            continue
        try:
            posts = await fetch_all_posts(uname, max_pages=max_pages)
        except Exception as e:
            logger.warning("backfill TG @%s: fetch error %s", uname, e)
            continue

        in_window: List[ParsedSignal] = []
        for post in posts:
            if not post.date:
                continue
            pd = _ensure_utc(post.date)
            if not (start <= pd < end):
                continue
            sig = parse_signal_from_text(post.text)
            if sig and sig.entry_price:
                sig.timestamp = pd
                in_window.append(sig)

        raw_posts += len([p for p in posts if p.date and start <= _ensure_utc(p.date) < end])
        st = persist_parsed_signals_for_channel(
            db,
            channel,
            in_window,
            posts_fetched=len(in_window),
            record_metrics=False,
            use_message_time_for_created_at=True,
        )
        aggregate_stats(total, st)
        if st.get("saved"):
            logger.info(
                "backfill TG @%s: posts_in_window=%s saved=%s",
                uname,
                len(in_window),
                st["saved"],
            )

    total["posts_in_window"] = raw_posts
    total["channels"] = len(channels)
    return total


async def backfill_reddit_window(
    db: Session,
    settings: Any,
    start: datetime,
    end: datetime,
    *,
    max_pages_per_sub: int = 40,
) -> Dict[str, Any]:
    if not getattr(settings, "COLLECT_REDDIT_IN_RUN_COLLECTION", True):
        return {"skipped": True, "reason": "COLLECT_REDDIT_IN_RUN_COLLECTION=false"}

    start = _ensure_utc(start)
    end = _ensure_utc(end)
    total: Dict[str, int] = {}

    for sub in CRYPTO_SUBREDDITS:
        try:
            res = await collect_reddit_signals_in_window(
                sub, start, end, max_pages=max_pages_per_sub, per_page=100
            )
        except Exception as e:
            logger.warning("backfill Reddit r/%s: %s", sub, e)
            continue

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
            record_metrics=False,
            use_message_time_for_created_at=True,
        )
        aggregate_stats(total, st)

    total["subreddits"] = len(CRYPTO_SUBREDDITS)
    return total


async def backfill_signals_for_window(
    db: Session,
    settings: Any,
    start: datetime,
    end: datetime,
    *,
    telegram_max_pages: int = 45,
    reddit_max_pages: int = 40,
) -> Dict[str, Any]:
    """Telegram + Reddit за один проход (один commit — вызывающий)."""
    out: Dict[str, Any] = {
        "start": _ensure_utc(start).isoformat(),
        "end": _ensure_utc(end).isoformat(),
    }
    out["telegram"] = await backfill_telegram_window(
        db, settings, start, end, max_pages=telegram_max_pages
    )
    out["reddit"] = await backfill_reddit_window(
        db, settings, start, end, max_pages_per_sub=reddit_max_pages
    )
    return out
