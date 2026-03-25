"""
Reddit signal scraper — collects crypto signals from subreddits.
Uses public RSS (recent) or JSON /new with pagination (historical windows).
"""
import logging
import random
import asyncio
import httpx
from typing import List, Optional, Tuple
from datetime import datetime, timezone
from app.services.telegram_scraper import (
    ParsedSignal,
    parse_signal_from_text,
    ChannelScrapeResult,
    HTTP_USER_AGENTS,
)

logger = logging.getLogger(__name__)

CRYPTO_SUBREDDITS = [
    "CryptoCurrency", "CryptoMarkets", "Bitcoin", "ethtrader",
    "SatoshiStreetBets", "CryptoMoonShots", "altcoin", "binance",
    "solana", "cardano", "ethereum", "defi", "BitcoinBeginners",
    "CryptoTechnology", "Bitcointrading", "CryptoCurrencyTrading",
    "Daytrading", "wallstreetbetscrypto", "CryptoCurrencies",
    "Crypto_Currency_News",
    # +10 for ROADMAP Signals
    "BitcoinMarkets", "EthTrader", "CryptoMoon", "SolanaTrading",
    "DeFi", "Chainlink", "Polkadot", "CosmosAirdrops",
    "Crypto_General", "BitcoinCash",
]


async def fetch_subreddit_posts(subreddit: str, limit: int = 25) -> List[dict]:
    """Fetch recent posts from a subreddit via RSS feed."""
    url = f"https://www.reddit.com/r/{subreddit}/new.rss"
    posts = []
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            r = await client.get(
                url,
                headers={"User-Agent": random.choice(HTTP_USER_AGENTS)},
            )
            if r.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(r.text, "html.parser")
                for entry in soup.find_all("entry")[:limit]:
                    title = entry.find("title")
                    content = entry.find("content")
                    updated = entry.find("updated")
                    link = entry.find("link")
                    posts.append({
                        "title": title.get_text() if title else "",
                        "text": BeautifulSoup(content.get_text(), "html.parser").get_text() if content else "",
                        "score": 0,
                        "created": datetime.fromisoformat(updated.get_text().replace("Z", "+00:00")) if updated else datetime.utcnow(),
                        "url": link.get("href", "") if link else "",
                        "author": "",
                    })
            else:
                logger.warning(f"Reddit r/{subreddit}: HTTP {r.status_code}")
    except Exception as e:
        logger.error(f"Reddit r/{subreddit} error: {e}")
    return posts


async def collect_reddit_signals(
    subreddit: str = "CryptoCurrency", limit: int = 50
) -> ChannelScrapeResult:
    """Fetch posts and extract trading signals from a subreddit."""
    posts = await fetch_subreddit_posts(subreddit, limit)
    signals: List[ParsedSignal] = []

    for post in posts:
        full_text = f"{post['title']}\n{post['text']}"
        sig = parse_signal_from_text(full_text)
        if sig and sig.entry_price:
            sig.timestamp = post["created"]
            sig.original_text = f"[Reddit r/{subreddit}] {post['title'][:200]}"
            signals.append(sig)

    logger.info(f"r/{subreddit}: {len(posts)} posts, {len(signals)} signals")
    return ChannelScrapeResult(posts_fetched=len(posts), signals=signals)


async def fetch_subreddit_new_json_pages(
    subreddit: str,
    *,
    start: datetime,
    end: datetime,
    max_pages: int = 40,
    per_page: int = 100,
    pause_sec: float = 0.45,
) -> List[dict]:
    """
    Посты r/{subreddit} в полуинтервале [start, end) по времени создания (UTC).
    Идём от new к старым через after=; останавливаемся, если страница целиком старше start.
    """
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)

    collected: List[dict] = []
    after: Optional[str] = None

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        for page in range(max_pages):
            params: dict = {"limit": str(per_page), "raw_json": "1"}
            if after:
                params["after"] = after
            url = f"https://www.reddit.com/r/{subreddit}/new.json"
            try:
                r = await client.get(
                    url,
                    params=params,
                    headers={"User-Agent": random.choice(HTTP_USER_AGENTS)},
                )
            except Exception as e:
                logger.warning("Reddit r/%s JSON page %s: %s", subreddit, page + 1, e)
                break

            if r.status_code != 200:
                logger.warning("Reddit r/%s JSON: HTTP %s", subreddit, r.status_code)
                break

            try:
                payload = r.json()
            except Exception as e:
                logger.warning("Reddit r/%s JSON parse: %s", subreddit, e)
                break

            data = payload.get("data") or {}
            children = data.get("children") or []
            if not children:
                break

            stop_paging = False
            for c in children:
                d = c.get("data") or {}
                created_utc = d.get("created_utc")
                if created_utc is None:
                    continue
                created = datetime.fromtimestamp(float(created_utc), tz=timezone.utc)
                if created >= end:
                    continue
                if created < start:
                    stop_paging = True
                    break
                title = (d.get("title") or "").strip()
                body = (d.get("selftext") or "").strip()
                link = (d.get("url") or "").strip()
                full_text = f"{title}\n{body}\n{link}".strip()
                collected.append(
                    {
                        "title": title,
                        "text": full_text,
                        "created": created,
                    }
                )

            after = data.get("after")
            if stop_paging or not after:
                break
            await asyncio.sleep(pause_sec)

    return collected


async def collect_reddit_signals_in_window(
    subreddit: str,
    start: datetime,
    end: datetime,
    *,
    max_pages: int = 40,
    per_page: int = 100,
) -> ChannelScrapeResult:
    """Как collect_reddit_signals, но только посты в [start, end) и с глубокой пагинацией JSON."""
    posts = await fetch_subreddit_new_json_pages(
        subreddit,
        start=start,
        end=end,
        max_pages=max_pages,
        per_page=per_page,
    )
    signals: List[ParsedSignal] = []
    for post in posts:
        full_text = post["text"] or post["title"]
        sig = parse_signal_from_text(full_text)
        if sig and sig.entry_price:
            sig.timestamp = post["created"]
            title = post["title"][:200] if post.get("title") else ""
            sig.original_text = f"[Reddit r/{subreddit}] {title}"
            signals.append(sig)

    logger.info(
        "r/%s window: %s posts in range, %s signals",
        subreddit,
        len(posts),
        len(signals),
    )
    return ChannelScrapeResult(posts_fetched=len(posts), signals=signals)


async def collect_all_reddit_signals() -> dict:
    """Collect signals from all crypto subreddits."""
    total_posts = 0
    total_signals = 0
    results = []

    for sub in CRYPTO_SUBREDDITS:
        res = await collect_reddit_signals(sub, limit=25)
        total_posts += res.posts_fetched
        total_signals += len(res.signals)
        if res.signals:
            results.append({"subreddit": sub, "signals": len(res.signals)})

    return {
        "subreddits": len(CRYPTO_SUBREDDITS),
        "posts_checked": total_posts,
        "signals_found": total_signals,
        "active_subs": results,
    }
