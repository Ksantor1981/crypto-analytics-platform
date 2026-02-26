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
from dataclasses import dataclass

logger = logging.getLogger(__name__)

CRYPTO_PAIRS = {
    "BTC": 1000, "ETH": 50, "BNB": 10, "SOL": 1, "ADA": 0.01,
    "XRP": 0.01, "DOT": 0.1, "DOGE": 0.001, "AVAX": 1, "MATIC": 0.01,
    "LINK": 0.1, "UNI": 0.1, "ATOM": 0.1, "LTC": 1, "NEAR": 0.1,
    "APT": 0.1, "ARB": 0.01, "OP": 0.01, "FTM": 0.01, "ALGO": 0.01,
    "FIL": 0.1, "INJ": 0.1, "TIA": 0.1, "SUI": 0.01, "SEI": 0.01,
    "JUP": 0.01, "WIF": 0.01, "PEPE": 0.0000001, "BONK": 0.0000001,
    "SHIB": 0.0000001, "ENA": 0.01, "IMX": 0.01, "AAVE": 1,
    "CRV": 0.01, "SAND": 0.01, "MANA": 0.01, "AXS": 0.1,
    "DYDX": 0.1, "GMX": 1, "SNX": 0.1, "COMP": 1, "MKR": 100,
    "RUNE": 0.1, "FET": 0.01, "RENDER": 0.1, "TAO": 10,
    "STX": 0.01, "TRX": 0.01, "TON": 0.1, "NOT": 0.001,
    "SXP": 0.01, "BAT": 0.01, "QSP": 0.001, "1INCH": 0.01,
}

LONG_KW = re.compile(r'\b(long|buy|buyy|лонг|покупка|купить|бай|adding\s+more)\b|📈|🟢|🚀', re.I)
SHORT_KW = re.compile(r'\b(short|sell|selll|шорт|продажа|продать|сел)\b|📉|🔴', re.I)

# Non-crypto assets to ignore
IGNORE_ASSETS = {"XAU", "XAUUSD", "GOLD", "OIL", "SPX", "NAS", "DXY", "EUR", "GBP", "JPY"}


@dataclass
class ParsedSignal:
    asset: str
    direction: str
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


async def fetch_channel_posts(username: str, limit: int = 20) -> List[ChannelPost]:
    """Fetch recent posts from a public Telegram channel."""
    url = f"https://t.me/s/{username}"
    posts = []
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            if resp.status_code != 200:
                return []
            soup = BeautifulSoup(resp.text, "html.parser")
            for msg in soup.select(".tgme_widget_message_wrap")[-limit:]:
                text_el = msg.select_one(".tgme_widget_message_text")
                if not text_el:
                    continue
                text = text_el.get_text(separator="\n").strip()
                date_el = msg.select_one(".tgme_widget_message_date time")
                date = None
                if date_el and date_el.get("datetime"):
                    try:
                        date = datetime.fromisoformat(date_el["datetime"].replace("Z", "+00:00"))
                    except ValueError:
                        pass
                views_el = msg.select_one(".tgme_widget_message_views")
                views = None
                if views_el:
                    vt = views_el.get_text().strip().replace("K", "000").replace("M", "000000")
                    try:
                        views = int(float(vt))
                    except ValueError:
                        pass
                posts.append(ChannelPost(text=text, date=date, views=views))
    except Exception as e:
        logger.error(f"Error fetching @{username}: {e}")
    return posts


def _detect_asset(text: str) -> Optional[str]:
    """Detect crypto asset from text, return e.g. 'SOL/USDT'."""
    text_upper = text.upper()
    for pair in sorted(CRYPTO_PAIRS.keys(), key=len, reverse=True):
        patterns = [
            rf'#{pair}\b',
            rf'\${pair}\b',
            rf'\b{pair}\s*/\s*USDT\b',
            rf'\b{pair}USDT\b',
            rf'\b{pair}\s*/\s*USD\b',
            rf'\b{pair}\s*/\s*BTC\b',
        ]
        for pat in patterns:
            if re.search(pat, text_upper):
                return f"{pair}/USDT"
    for pair in sorted(CRYPTO_PAIRS.keys(), key=len, reverse=True):
        if re.search(rf'\b{pair}\b', text_upper):
            if pair not in ("NOT", "OP", "AT"):
                return f"{pair}/USDT"
    return None


def _parse_price(text: str, pattern: str) -> Optional[float]:
    """Extract price from text using pattern."""
    m = re.search(pattern, text, re.I | re.M)
    if m:
        raw = m.group(1).replace(",", "").replace(" ", "")
        if raw.endswith("k"):
            raw = raw[:-1]
            try:
                return float(raw) * 1000
            except ValueError:
                return None
        try:
            return float(raw)
        except ValueError:
            pass
    return None


def _validate_price(price: float, asset: str) -> bool:
    """Check if price is reasonable for asset."""
    pair = asset.replace("/USDT", "").replace("/USD", "")
    min_price = CRYPTO_PAIRS.get(pair, 0.0001)
    max_price = min_price * 100000
    return min_price * 0.1 <= price <= max_price


def parse_signal_from_text(text: str) -> Optional[ParsedSignal]:
    """Extract trading signal from message text."""
    # Skip non-crypto assets
    text_upper = text.upper()
    for ignore in IGNORE_ASSETS:
        if ignore in text_upper and not any(c in text_upper for c in ["BTC", "ETH", "SOL"]):
            return None

    asset = _detect_asset(text)
    if not asset:
        return None

    direction = None
    if LONG_KW.search(text):
        direction = "LONG"
    if SHORT_KW.search(text):
        direction = "SHORT" if not direction else direction

    if not direction:
        return None

    entry_patterns = [
        r'(?:entry|вход|enter|price|цена)\s*(?:price|zone|зона)?[:\s]*\$?([\d]+[,.]?\d*k?)',
        r'(?:buy|купить|long|лонг)\s*(?:at|по|@|zone|from)?[:\s]*\$?([\d]+[,.]?\d*k?)',
        r'(?:sell|продать|short|шорт)\s*(?:at|по|@|from)?[:\s]*\$?([\d]+[,.]?\d*k?)',
        r'\bCP\b[:\s)]*\$?([\d]+[,.]?\d*k?)',
        r'(?:entry|вход)\s*[:]\s*\$?([\d]+[,.]?\d*k?)\s*[-–]',
    ]
    tp_patterns = [
        r'(?:tp|take.profit|тейк|цель|target)\s*\d?[:\s]*\$?([\d]+[,.]?\d*k?)',
        r'(?:targets?|цели)[:\s]*\$?([\d]+[,.]?\d*k?)',
    ]
    sl_patterns = [
        r'(?:sl|stop.loss|стоп|стоп.лосс|stoploss)[:\s]*\$?([\d]+[,.]?\d*k?)',
    ]

    entry_price = None
    for pat in entry_patterns:
        p = _parse_price(text, pat)
        if p and _validate_price(p, asset):
            entry_price = p
            break

    take_profit = None
    for pat in tp_patterns:
        p = _parse_price(text, pat)
        if p and _validate_price(p, asset):
            take_profit = p
            break

    stop_loss = None
    for pat in sl_patterns:
        p = _parse_price(text, pat)
        if p and _validate_price(p, asset):
            stop_loss = p
            break

    dollar_prices = re.findall(r'\$([\d]+[,.]?\d*k?)', text)
    valid_prices = []
    for raw in dollar_prices:
        try:
            val = float(raw.replace(",", "").replace("k", "")) * (1000 if raw.endswith("k") else 1)
            if _validate_price(val, asset):
                valid_prices.append(val)
        except ValueError:
            pass

    if not entry_price and valid_prices:
        entry_price = valid_prices[0]
    if not take_profit and len(valid_prices) >= 2:
        take_profit = valid_prices[1]

    confidence = 0.4
    if entry_price:
        confidence = 0.6
        if take_profit:
            confidence = 0.75
        if stop_loss:
            confidence = 0.85

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
    """Fetch and extract signals from a public Telegram channel."""
    posts = await fetch_channel_posts(username)
    signals = []
    for post in posts:
        sig = parse_signal_from_text(post.text)
        if sig:
            sig.timestamp = post.date
            signals.append(sig)
    logger.info(f"@{username}: {len(posts)} posts, {len(signals)} signals")
    return signals
