#!/usr/bin/env python3
"""
Collect real signals from PUBLIC Telegram channels via t.me/s (web preview),
for the last N days, without Telethon/user auth.

Limitations:
- Works only for public channels where t.me/s/<username> is accessible.
- Telegram может rate-limit по IP; скрипт делает паузы между каналами.

Pipeline:
1) Scrape posts with pagination (deep_collector.fetch_all_posts)
2) Filter by date (last N days)
3) Parse signal from text (telegram_scraper.parse_signal_from_text)
4) Persist into DB (collection_pipeline.persist_parsed_signals_for_channel)

Run (inside backend container):
  docker exec crypto-analytics-backend python scripts/public_collect_last_30d.py --days 30
"""
import argparse
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))
# workers/ lives at project root
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.channel import Channel
from app.services.collection_pipeline import persist_parsed_signals_for_channel
from app.services.deep_collector import fetch_all_posts
from app.services.telegram_scraper import parse_signal_from_text


def _normalize_username(u: str) -> str:
    u = (u or "").strip()
    if not u:
        return ""
    u = u[1:] if u.startswith("@") else u
    return u


def ensure_channel(db, username: str, name: str = "") -> Channel:
    username = _normalize_username(username)
    ch = db.query(Channel).filter(Channel.username == username).first()
    if ch:
        ch.is_active = True
        ch.platform = ch.platform or "telegram"
        return ch
    ch = Channel(
        username=username,
        name=name or username,
        url=f"https://t.me/{username}",
        platform="telegram",
        description=f"Telegram channel @{username} (public web preview)",
        category="telegram",
        is_active=True,
        status="active",
        signals_count=0,
    )
    db.add(ch)
    db.flush()
    return ch


async def collect_channel(username: str, days_back: int, max_pages: int) -> tuple[int, int, int]:
    """
    Returns: (posts_total, posts_in_window, parsed_signals)
    """
    uname = _normalize_username(username)
    posts = await fetch_all_posts(uname, max_pages=max_pages)
    since = datetime.now(timezone.utc) - timedelta(days=days_back)
    in_window = []
    for p in posts:
        if p.date and p.date >= since:
            in_window.append(p)
    parsed = 0
    signals = []
    for p in in_window:
        sig = parse_signal_from_text(p.text)
        if sig and sig.entry_price:
            sig.timestamp = p.date
            sig.telegram_message_id = p.message_id
            sig.original_text = p.text
            signals.append(sig)
            parsed += 1
    return len(posts), len(in_window), parsed, signals


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--max-pages", type=int, default=20, help="pagination pages per channel (increase if high volume)")
    ap.add_argument("--sleep-ms", type=int, default=800, help="sleep between channels to reduce rate-limit")
    args = ap.parse_args()

    settings = get_settings()
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = Session()
    try:
        # Source of truth: DB channels marked as telegram + active
        db_channels = (
            db.query(Channel)
            .filter(Channel.platform == "telegram", Channel.is_active == True)
            .all()
        )
        usernames = []
        for ch in db_channels:
            uname = ch.username or (ch.url or "").rstrip("/").split("/")[-1]
            uname = _normalize_username(uname)
            if uname:
                usernames.append((uname, ch.name or uname))

        if not usernames:
            print("ERROR: No active telegram channels in DB (channels.platform='telegram').")
            print("Add channels in DB first, then re-run this script.")
            raise SystemExit(2)

        total_saved = 0
        total_parsed = 0
        for uname, name in usernames:
            ch = ensure_channel(db, uname, name=name)
            posts_total, posts_window, parsed_count, signals = await collect_channel(
                uname, days_back=args.days, max_pages=args.max_pages
            )
            total_parsed += parsed_count
            st = persist_parsed_signals_for_channel(
                db,
                ch,
                signals,
                posts_fetched=posts_window,
                record_metrics=True,
                use_message_time_for_created_at=True,
            )
            db.commit()
            total_saved += st.get("saved", 0)
            print(
                f"@{ch.username}: posts={posts_total} window={posts_window} parsed={parsed_count} "
                f"saved={st.get('saved',0)} dup={st.get('skipped_duplicate',0)} no_entry={st.get('skipped_no_entry',0)}"
            )
            await asyncio.sleep(max(0, args.sleep_ms) / 1000.0)

        print(f"DONE. channels={len(usernames)} parsed_total={total_parsed} saved_total={total_saved}")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
