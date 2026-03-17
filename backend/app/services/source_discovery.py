"""
Automatic source discovery & maintenance.

Goal: add new sources without manual input and keep sources list актуальным
by periodically enabling/disabling based on observed signal flow.

No new API keys are required:
- Reddit discovery uses public RSS endpoints.
- Telegram discovery uses public directory search pages (best-effort).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models.channel import Channel
from app.models.signal import Signal
from app.services.telegram_scraper import parse_signal_from_text

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredSource:
    platform: str
    username: str
    name: str
    url: str
    description: Optional[str] = None
    signals_found: int = 0


def _utcnow() -> datetime:
    return datetime.utcnow()


async def _fetch_rss(url: str) -> str:
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code}")
        return r.text


def _extract_subreddit_from_url(url: str) -> Optional[str]:
    # Examples:
    # https://www.reddit.com/r/CryptoCurrency/comments/...
    m = re.search(r"reddit\.com/r/([^/]+)/", url, re.I)
    return m.group(1) if m else None


async def discover_reddit_sources(
    queries: Iterable[str],
    per_query_limit: int = 25,
    min_signals_per_subreddit: int = 2,
) -> List[DiscoveredSource]:
    """
    Discover subreddits that produce parseable trading-signal-like content
    using Reddit public search RSS (no auth).
    """
    # Map subreddit -> signals_found
    counts: Dict[str, int] = {}

    for q in queries:
        # Reddit search RSS across all
        # Note: spaces are OK; Reddit will interpret query string.
        url = f"https://www.reddit.com/search.rss?q={quote(q)}&sort=new"
        try:
            xml = await _fetch_rss(url)
        except Exception as e:
            logger.warning("[Discovery] Reddit search RSS failed for query=%r: %s", q, e)
            continue

        soup = BeautifulSoup(xml, "xml")
        entries = soup.find_all("entry")[:per_query_limit]
        for entry in entries:
            title = (entry.find("title").get_text() if entry.find("title") else "") or ""
            content = (entry.find("content").get_text() if entry.find("content") else "") or ""
            link = entry.find("link")
            href = link.get("href") if link else ""
            sub = _extract_subreddit_from_url(href or "")
            if not sub:
                continue

            text = f"{title}\n{BeautifulSoup(content, 'html.parser').get_text()}"
            sig = parse_signal_from_text(text)
            if sig and sig.entry_price:
                counts[sub] = counts.get(sub, 0) + 1

    discovered: List[DiscoveredSource] = []
    for sub, n in sorted(counts.items(), key=lambda kv: kv[1], reverse=True):
        if n < min_signals_per_subreddit:
            continue
        discovered.append(
            DiscoveredSource(
                platform="reddit",
                username=f"r_{sub}",
                name=f"r/{sub}",
                url=f"https://reddit.com/r/{sub}",
                description=f"Auto-discovered from Reddit search (signals_found={n})",
                signals_found=n,
            )
        )
    return discovered


async def discover_telegram_sources_tgstat(
    keywords: Iterable[str],
    per_keyword_limit: int = 15,
) -> List[DiscoveredSource]:
    """
    Best-effort Telegram channel discovery via public directory search pages.

    This does not require Telegram API keys, but is inherently less reliable.
    """
    discovered: Dict[str, DiscoveredSource] = {}

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        for kw in keywords:
            # tgstat search (best-effort, may change)
            url = f"https://tgstat.com/search?q={quote(kw)}"
            try:
                r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code != 200:
                    logger.warning("[Discovery] tgstat HTTP %s for kw=%r", r.status_code, kw)
                    continue
                soup = BeautifulSoup(r.text, "html.parser")

                # Heuristic: pick links that look like /channel/@username or have t.me links
                links = soup.find_all("a", href=True)
                candidates: List[Tuple[str, str]] = []
                for a in links:
                    href = a["href"]
                    text = a.get_text(" ", strip=True) or ""
                    m = re.search(r"t\.me/([A-Za-z0-9_]{4,})", href)
                    if m:
                        candidates.append((m.group(1), text))
                        continue
                    m2 = re.search(r"/channel/(@?[A-Za-z0-9_]{4,})", href)
                    if m2:
                        candidates.append((m2.group(1).lstrip("@"), text))

                # Dedup and cap
                seen = set()
                for username, title in candidates:
                    if username in seen:
                        continue
                    seen.add(username)
                    if len(seen) > per_keyword_limit:
                        break
                    if username not in discovered:
                        discovered[username] = DiscoveredSource(
                            platform="telegram",
                            username=username,
                            name=title or username,
                            url=f"https://t.me/{username}",
                            description=f"Auto-discovered by keyword={kw!r}",
                        )
            except Exception as e:
                logger.warning("[Discovery] tgstat search failed for kw=%r: %s", kw, e)

    return list(discovered.values())


def upsert_sources(db: Session, sources: Iterable[DiscoveredSource]) -> Dict[str, int]:
    """
    Insert new channels or update existing, and auto-activate them.
    We never delete rows — only (de)activate.
    """
    added = 0
    updated = 0
    now = _utcnow()

    for s in sources:
        existing = db.query(Channel).filter(Channel.username == s.username).first()
        if existing:
            changed = False
            if existing.platform != s.platform:
                existing.platform = s.platform
                changed = True
            if s.url and existing.url != s.url:
                existing.url = s.url
                changed = True
            if s.name and existing.name != s.name:
                existing.name = s.name
                changed = True
            if s.description and existing.description != s.description:
                existing.description = s.description
                changed = True
            if existing.is_active is False:
                existing.is_active = True
                existing.status = "active"
                existing.disabled_reason = None
                changed = True
            existing.last_checked_at = now
            if changed:
                updated += 1
            continue

        ch = Channel(
            username=s.username,
            name=s.name or s.username,
            url=s.url,
            description=s.description,
            platform=s.platform,
            is_active=True,
            status="active",
            is_candidate=False,
            discovered_at=now,
            last_checked_at=now,
            priority=1,
        )
        db.add(ch)
        added += 1

    return {"added": added, "updated": updated}


def deactivate_stale_sources(
    db: Session,
    days_without_signals: int = 14,
) -> Dict[str, int]:
    """
    Auto-cleanup: disable sources that haven't produced signals for N days.
    No deletion — just is_active=False + status + reason.
    """
    now = _utcnow()
    cutoff = now - timedelta(days=days_without_signals)
    deactivated = 0

    channels = db.query(Channel).filter(Channel.is_active == True).all()
    for ch in channels:
        recent = (
            db.query(Signal)
            .filter(Signal.channel_id == ch.id, Signal.created_at >= cutoff)
            .count()
        )
        ch.last_checked_at = now
        if recent > 0:
            ch.last_new_signal_at = now  # approximation; we only track that it was active within window
            continue

        ch.is_active = False
        ch.status = "inactive"
        ch.disabled_reason = f"auto: no signals in last {days_without_signals}d"
        deactivated += 1

    return {"deactivated": deactivated}

