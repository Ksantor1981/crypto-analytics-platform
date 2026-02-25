"""
Real Telegram channel scraper — parses public channels via t.me/s/ web preview.
No API keys required.
"""
import re
import logging
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ParsedSignal:
    asset: str
    direction: str  # LONG / SHORT
    entry_price: Optional[float] = None
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    confidence: float = 0.5
    original_text: str = ""
    timestamp: Optional[datetime] = None


@dataclass
class ChannelPost:
    text: str
    date: Optional[datetime] = None
    views: Optional[int] = None


CRYPTO_PAIRS = [
    "BTC", "ETH", "BNB", "SOL", "ADA", "XRP", "DOT", "DOGE", "AVAX", "MATIC",
    "LINK", "UNI", "ATOM", "LTC", "NEAR", "APT", "ARB", "OP", "FTM", "ALGO",
    "FIL", "INJ", "TIA", "SUI", "SEI", "JUP", "WIF", "PEPE", "BONK", "SHIB",
]

LONG_KEYWORDS = ["long", "buy", "лонг", "покупка", "купить", "бай", "📈", "🟢", "🚀"]
SHORT_KEYWORDS = ["short", "sell", "шорт", "продажа", "продать", "сел", "📉", "🔴"]


async def fetch_channel_posts(username: str, limit: int = 20) -> List[ChannelPost]:
    """Fetch recent posts from a public Telegram channel via web preview."""
    url = f"https://t.me/s/{username}"
    posts = []

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            resp = await client.get(url, headers=headers)

            if resp.status_code != 200:
                logger.warning(f"Channel @{username}: HTTP {resp.status_code}")
                return []

            soup = BeautifulSoup(resp.text, "html.parser")
            messages = soup.select(".tgme_widget_message_wrap")

            for msg in messages[-limit:]:
                text_el = msg.select_one(".tgme_widget_message_text")
                date_el = msg.select_one(".tgme_widget_message_date time")
                views_el = msg.select_one(".tgme_widget_message_views")

                if not text_el:
                    continue

                text = text_el.get_text(separator="\n").strip()
                date = None
                if date_el and date_el.get("datetime"):
                    try:
                        date = datetime.fromisoformat(
                            date_el["datetime"].replace("Z", "+00:00")
                        )
                    except ValueError:
                        pass

                views = None
                if views_el:
                    views_text = views_el.get_text().strip().replace("K", "000").replace("M", "000000")
                    try:
                        views = int(float(views_text))
                    except ValueError:
                        pass

                posts.append(ChannelPost(text=text, date=date, views=views))

    except Exception as e:
        logger.error(f"Error fetching @{username}: {e}")

    return posts


def parse_signal_from_text(text: str) -> Optional[ParsedSignal]:
    """Extract trading signal from message text."""
    text_lower = text.lower()

    asset = None
    for pair in CRYPTO_PAIRS:
        patterns = [
            rf'\b{pair}\b',
            rf'\b{pair}/USDT\b',
            rf'\b{pair}USDT\b',
            rf'\b{pair}/USD\b',
            rf'\b\${pair}\b',
        ]
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                asset = f"{pair}/USDT"
                break
        if asset:
            break

    if not asset:
        return None

    direction = None
    for kw in LONG_KEYWORDS:
        if kw in text_lower:
            direction = "LONG"
            break
    if not direction:
        for kw in SHORT_KEYWORDS:
            if kw in text_lower:
                direction = "SHORT"
                break

    if not direction:
        return None

    def extract_prices(text_block: str) -> List[float]:
        """Extract all price-like numbers from text."""
        nums = re.findall(r'(?<!\w)\$?([\d]{1,10}(?:\.[\d]{1,8})?)\b', text_block)
        prices = []
        for n in nums:
            try:
                val = float(n)
                if 0.0001 < val < 1000000:
                    prices.append(val)
            except ValueError:
                pass
        return prices

    def extract_price(patterns: List[str]) -> Optional[float]:
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    val = float(match.group(1).replace(",", ""))
                    if 0.0001 < val < 1000000:
                        return val
                except (ValueError, IndexError):
                    pass
        return None

    entry_price = extract_price([
        r'(?:entry|вход|enter|price|цена)\s*(?:price|zone|зона)?[:\s]*\$?([\d]+\.?\d*)',
        r'(?:buy|купить|покупка|лонг|long)\s*(?:at|по|@|zone|зона)?[:\s]*\$?([\d]+\.?\d*)',
        r'(?:sell|продать|шорт|short)\s*(?:at|по|@)?[:\s]*\$?([\d]+\.?\d*)',
        r'\bCP\b[:\s)]*\$?([\d]+\.?\d*)',
        r'(?:вход|entry)[:\s]*([\d]+\.?\d*)\s*[-–]\s*[\d]+\.?\d*',
    ])

    take_profit = extract_price([
        r'(?:tp|take\s*profit|тейк|цель)\s*\d?[:\s]*\$?([\d]+\.?\d*)',
        r'(?:tp1|тп1|tp\s*1)[:\s]*\$?([\d]+\.?\d*)',
        r'(?:targets?|цели)[:\s]*\$?([\d]+\.?\d*)',
    ])

    stop_loss = extract_price([
        r'(?:sl|stop\s*loss|стоп|стоп.лосс|stoploss)[:\s]*\$?([\d]+\.?\d*)',
    ])

    if not entry_price:
        all_prices = extract_prices(text)
        if len(all_prices) >= 2 and direction:
            entry_price = all_prices[0]
            if not take_profit and len(all_prices) >= 2:
                take_profit = all_prices[1]
            if not stop_loss and len(all_prices) >= 3:
                stop_loss = all_prices[-1]

    confidence = 0.5
    if entry_price and take_profit and stop_loss:
        confidence = 0.85
    elif entry_price and (take_profit or stop_loss):
        confidence = 0.7
    elif entry_price:
        confidence = 0.6

    return ParsedSignal(
        asset=asset,
        direction=direction,
        entry_price=entry_price,
        take_profit=take_profit,
        stop_loss=stop_loss,
        confidence=confidence,
        original_text=text[:500],
    )


async def collect_signals_from_channel(username: str) -> List[ParsedSignal]:
    """Fetch posts and extract trading signals from a public Telegram channel."""
    posts = await fetch_channel_posts(username)
    signals = []

    for post in posts:
        signal = parse_signal_from_text(post.text)
        if signal:
            signal.timestamp = post.date
            signals.append(signal)

    logger.info(f"@{username}: {len(posts)} posts, {len(signals)} signals found")
    return signals
