"""
Reddit signal scraper — collects crypto signals from subreddits.
Uses public JSON API (no auth required).
"""
import logging
import httpx
from typing import List
from datetime import datetime
from app.services.telegram_scraper import ParsedSignal, parse_signal_from_text

logger = logging.getLogger(__name__)

CRYPTO_SUBREDDITS = [
    "CryptoCurrency", "CryptoMarkets", "Bitcoin", "ethtrader",
    "SatoshiStreetBets", "CryptoMoonShots", "altcoin", "binance",
    "solana", "cardano", "ethereum", "defi", "BitcoinBeginners",
    "CryptoTechnology", "Bitcointrading", "CryptoCurrencyTrading",
    "Daytrading", "wallstreetbetscrypto", "CryptoCurrencies",
    "Crypto_Currency_News",
]


async def fetch_subreddit_posts(subreddit: str, limit: int = 25) -> List[dict]:
    """Fetch recent posts from a subreddit via RSS feed."""
    url = f"https://www.reddit.com/r/{subreddit}/new.rss"
    posts = []
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            r = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
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


async def collect_reddit_signals(subreddit: str = "CryptoCurrency", limit: int = 50) -> List[ParsedSignal]:
    """Fetch posts and extract trading signals from a subreddit."""
    posts = await fetch_subreddit_posts(subreddit, limit)
    signals = []

    for post in posts:
        full_text = f"{post['title']}\n{post['text']}"
        sig = parse_signal_from_text(full_text)
        if sig and sig.entry_price:
            sig.timestamp = post["created"]
            sig.original_text = f"[Reddit r/{subreddit}] {post['title'][:200]}"
            signals.append(sig)

    logger.info(f"r/{subreddit}: {len(posts)} posts, {len(signals)} signals")
    return signals


async def collect_all_reddit_signals() -> dict:
    """Collect signals from all crypto subreddits."""
    total_posts = 0
    total_signals = 0
    results = []

    for sub in CRYPTO_SUBREDDITS:
        sigs = await collect_reddit_signals(sub, limit=25)
        total_posts += 25
        total_signals += len(sigs)
        if sigs:
            results.append({"subreddit": sub, "signals": len(sigs)})

    return {
        "subreddits": len(CRYPTO_SUBREDDITS),
        "posts_checked": total_posts,
        "signals_found": total_signals,
        "active_subs": results,
    }
