"""
Real Telegram channel scraper — parses public channels via t.me/s/ web preview.
No API keys required.
"""
import re
import logging
import random
import httpx
import os
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

# Ротация User-Agent снижает риск блокировок при массовом сборе
HTTP_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]

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

# News/digest keywords — skip posts that look like news, not signals
NEWS_SKIP_KW = re.compile(
    r'\b(Trump|Congress|Harvard|Bank of America|acquired|sold|increased|'
    r'Weekly Digest|market digest|portfolio|ETF|insider trading|'
    r'\$[\d.]+ (?:million|mill|billion|bn)\b|worth \$[\d.]+\s*(?:million|mill))',
    re.I
)

# DeFi / news-style — not a trading signal (protocol news, announcements)
DEFI_NEWS_LIKE = re.compile(
    r'\b(protocol|TVL|launch|audit|announcement|airdrop|governance|'
    r'ecosystem|partnership|integration|mainnet|testnet|upgrade|'
    r'listing|delisting|halving|conference|summit)\b',
    re.I
)
MIN_TEXT_LEN_FOR_STRICT_SIGNAL = 120  # below this, allow signal without TP/SL

# Garbage / spam / non-signal content — filter out
GARBAGE_SKIP_KW = re.compile(
    r'\b(join\s+channel|join\s+group|t\.me/|telegram\.me/join|'
    r'100%\s*free|guaranteed\s*profit|no\s*loss|risk.?free|'
    r'winner\s*winners|pump\s*dump\s*scheme|airdrop|giveaway|'
    r'scam|phishing|rug\s*pull|fake\s*admin|copy\s*trading\s*scam|'
    r'\d+\s*people\s*(?:joined|left)|DM\s*me|contact\s*admin|'
    r'lottery|raffle|referral\s*only|invite\s*\d+\s*people)',
    re.I
)

# Minimum length for signal text — too short = likely spam (8 allows "#BTC LONG", "$ETH SHORT from $2100")
MIN_SIGNAL_TEXT_LEN = 8

# Реалистичные диапазоны цен по тикерам (min, max) USD
PRICE_RANGES = {
    "BTC": (10000, 250000), "ETH": (500, 15000), "BNB": (100, 5000),
    "SOL": (5, 500), "ADA": (0.1, 10), "XRP": (0.1, 5), "DOT": (2, 50),
    "DOGE": (0.01, 2), "AVAX": (5, 200), "LINK": (5, 100), "UNI": (2, 50),
    "LTC": (30, 500), "NEAR": (1, 30), "APT": (5, 50), "ARB": (0.5, 5),
    "OP": (0.5, 5), "SUI": (0.5, 20), "PEPE": (1e-8, 0.0001),
    "SHIB": (1e-8, 0.0001), "MKR": (1000, 20000), "RUNE": (1, 50),
}
# Default для неизвестных: min из CRYPTO_PAIRS*0.1, max = min*1000


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
    telegram_message_id: Optional[str] = None
    entry_zone_low: Optional[float] = None
    entry_zone_high: Optional[float] = None


@dataclass
class ChannelPost:
    text: str
    date: Optional[datetime] = None
    views: Optional[int] = None
    message_id: Optional[str] = None
    image_urls: List[str] = field(default_factory=list)


@dataclass
class ChannelScrapeResult:
    """Результат сбора: сколько постов с HTML и сколько прошло текстовый парсер."""

    posts_fetched: int
    signals: List[ParsedSignal] = field(default_factory=list)
    # Все посты со страницы t.me/s (для shadow raw layer, см. docs/DATA_PLANE_MIGRATION.md)
    posts: List[ChannelPost] = field(default_factory=list)
    # Посты Reddit (dict из RSS/JSON) — shadow raw layer
    reddit_posts: List[Dict[str, Any]] = field(default_factory=list)


def _extract_telegram_message_id(msg_block) -> Optional[str]:
    """ID поста из ссылки вида https://t.me/channel/12345."""
    link = msg_block.select_one("a.tgme_widget_message_date")
    if not link:
        link = msg_block.select_one(".tgme_widget_message_date")
    href = (link.get("href") if link else None) or ""
    m = re.search(r"/(\d+)(?:\?|$)", href)
    return m.group(1) if m else None


def _extract_image_urls(msg_block) -> List[str]:
    """
    Extract image URLs from Telegram web-preview message block.
    Supports:
    - <a class="tgme_widget_message_photo_wrap" style="background-image:url('...')">
    - <img ... src="...">
    """
    urls: List[str] = []
    try:
        # background-image:url('...') wrapper
        for a in msg_block.select(".tgme_widget_message_photo_wrap"):
            style = (a.get("style") or "").strip()
            m = re.search(r"url\\(['\\\"]?(https?://[^'\\\"\\)]+)['\\\"]?\\)", style)
            if m:
                urls.append(m.group(1))
        # direct <img> tags (some layouts)
        for img in msg_block.select("img"):
            src = (img.get("src") or "").strip()
            if src.startswith("http"):
                urls.append(src)
    except Exception:
        return []
    # Dedup preserve order
    seen = set()
    out: List[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _extract_caption_or_alt_text(msg_block) -> str:
    """
    Try to extract caption/alt text from media-only posts in t.me/s HTML.
    This helps when Telegram renders a post with media but without
    `.tgme_widget_message_text` (or when text is only in attributes).
    """
    parts: List[str] = []
    try:
        # Some layouts still store caption in alternative containers
        for sel in (
            ".tgme_widget_message_caption",
            ".tgme_widget_message_text",
            ".tgme_widget_message_poll",
        ):
            el = msg_block.select_one(sel)
            if el:
                txt = el.get_text(separator="\n").strip()
                if txt:
                    parts.append(txt)

        # Media attributes
        for tag in msg_block.select("img"):
            for attr in ("alt", "title", "aria-label"):
                v = (tag.get(attr) or "").strip()
                if v:
                    parts.append(v)
        for tag in msg_block.select("a.tgme_widget_message_photo_wrap"):
            for attr in ("title", "aria-label"):
                v = (tag.get(attr) or "").strip()
                if v:
                    parts.append(v)
    except Exception:
        return ""

    # Dedup preserve order
    seen = set()
    out: List[str] = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return "\n".join(out).strip()


async def fetch_channel_posts(username: str, limit: int = 20) -> List[ChannelPost]:
    """Fetch recent posts from a public Telegram channel."""
    url = f"https://t.me/s/{username}"
    posts = []
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(
                url,
                headers={"User-Agent": random.choice(HTTP_USER_AGENTS)},
            )
            if resp.status_code != 200:
                return []
            soup = BeautifulSoup(resp.text, "html.parser")
            for msg in soup.select(".tgme_widget_message_wrap")[-limit:]:
                text_el = msg.select_one(".tgme_widget_message_text")
                text = ""
                if text_el:
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
                mid = _extract_telegram_message_id(msg)
                image_urls = _extract_image_urls(msg)
                if not text and image_urls:
                    # media-only post: try caption/alt from html
                    text = _extract_caption_or_alt_text(msg)
                # Keep posts that have either text OR images (OCR fallback)
                if not text and not image_urls:
                    continue
                posts.append(
                    ChannelPost(text=text, date=date, views=views, message_id=mid, image_urls=image_urls)
                )
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


def _normalize_price_token(raw: str) -> Optional[float]:
    """Число из токена цены: 65,500 (тысячи), 0,42 (евро-десятичные), 12k."""
    if not raw:
        return None
    s = raw.strip().replace(" ", "")
    mult = 1000 if s.lower().endswith("k") else 1
    if mult == 1000:
        s = s[:-1]
    if "," in s and "." not in s:
        parts = s.split(",")
        if len(parts) == 2:
            a, b = parts[0], parts[1]
            # US-стиль тысяч: 65,500 или 1,234
            if len(b) == 3 and a.isdigit() and b.isdigit() and len(a) <= 3:
                s = a + b
            else:
                s = a + "." + b
        else:
            s = "".join(parts)
    else:
        s = s.replace(",", "")
    try:
        return float(s) * mult
    except ValueError:
        return None


def _parse_price(text: str, pattern: str) -> Optional[float]:
    """Extract price from text using pattern (первая группа — токен цены)."""
    m = re.search(pattern, text, re.I | re.M)
    if m:
        return _normalize_price_token(m.group(1))
    return None


def _parse_price_two_groups(text: str, pattern: str) -> Optional[Tuple[float, float]]:
    """Две цены из паттерна (зона входа)."""
    m = re.search(pattern, text, re.I | re.M)
    if not m:
        return None
    a = _normalize_price_token(m.group(1))
    b = _normalize_price_token(m.group(2))
    if a is None or b is None:
        return None
    return (a, b)


def _parse_entry_zone(text: str, asset: str) -> Optional[Tuple[float, float]]:
    """Диапазон входа: 0.42-0.44, entry zone: 1,2 - 1,25, between X and Y."""
    zone_patterns = [
        r"(?:entry\s*zone|зона\s*входа|entry\s*range|диапазон\s*входа)[:\s]*"
        r"\$?([\d\s]+[,.]?\d*k?)\s*[-–—]\s*\$?([\d\s]+[,.]?\d*k?)",
        r"(?:entry|вход|zone|зона)\s*(?:range|диапазон)?[:\s]*"
        r"\$?([\d\s]+[,.]?\d*k?)\s*[-–—]\s*\$?([\d\s]+[,.]?\d*k?)",
        r"\$?([\d\s]+[,.]?\d*k?)\s*[-–—]\s*\$?([\d\s]+[,.]?\d*k?)\s*(?:entry|вход|zone|зона)?",
        r"between\s+\$?([\d\s]+[,.]?\d*k?)\s+and\s+\$?([\d\s]+[,.]?\d*k?)",
    ]
    for pat in zone_patterns:
        pair = _parse_price_two_groups(text, pat)
        if not pair:
            continue
        lo, hi = min(pair[0], pair[1]), max(pair[0], pair[1])
        mid = (lo + hi) / 2
        if _validate_price(mid, asset) and _validate_price(lo, asset) and _validate_price(hi, asset):
            if not _price_in_million_context(text, mid):
                return (lo, hi)
    return None


def _validate_price(price: float, asset: str) -> bool:
    """Check if price is reasonable for asset."""
    pair = asset.replace("/USDT", "").replace("/USD", "")
    if pair in PRICE_RANGES:
        lo, hi = PRICE_RANGES[pair]
        return lo <= price <= hi
    min_price = CRYPTO_PAIRS.get(pair, 0.0001)
    max_price = min_price * 10000
    return min_price * 0.5 <= price <= max_price


def _is_news_or_digest(text: str) -> bool:
    """Skip news/digest posts — not real trading signals."""
    if NEWS_SKIP_KW.search(text):
        return True
    return False


def _is_garbage(text: str) -> bool:
    """Filter spam/garbage — not real signals."""
    if GARBAGE_SKIP_KW.search(text):
        return True
    if len(text.strip()) < MIN_SIGNAL_TEXT_LEN:
        return True
    return False


def _price_in_million_context(text: str, price: float) -> bool:
    """True if this price appears next to million/mill (e.g. $168.4 million)."""
    # Match "168.4" or "168" near "million"/"mill"
    num_str = str(int(price)) if price == int(price) else str(price).rstrip("0").rstrip(".")
    pat = rf'\$?{re.escape(num_str)}\s*(?:million|mill|bn|billion)\b'
    return bool(re.search(pat, text, re.I))


def parse_signal_from_text(text: str) -> Optional[ParsedSignal]:
    """Extract trading signal from message text."""
    if _is_news_or_digest(text):
        return None
    if _is_garbage(text):
        return None
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

    entry_zone_low: Optional[float] = None
    entry_zone_high: Optional[float] = None
    entry_price = None

    # Сначала зона входа (иначе «entry zone: 0.42-0.44» ловится как одно число 0.42)
    z = _parse_entry_zone(text, asset)
    if z:
        entry_zone_low, entry_zone_high = z[0], z[1]
        mid = (entry_zone_low + entry_zone_high) / 2
        if _validate_price(mid, asset) and not _price_in_million_context(text, mid):
            entry_price = mid

    entry_patterns = [
        r'(?:entry|вход|enter|price|цена)\s*(?:price|zone|зона)?[:\s]*\$?([\d\s]+[,.]?\d*k?)',
        r'(?:buy|купить|long|лонг)\s*(?:at|по|@|zone|from)?[:\s]*\$?([\d\s]+[,.]?\d*k?)',
        r'(?:sell|продать|short|шорт)\s*(?:at|по|@|from)?[:\s]*\$?([\d\s]+[,.]?\d*k?)',
        r'\bCP\b[:\s)]*\$?([\d\s]+[,.]?\d*k?)',
        r'(?:entry|вход)\s*[:]\s*\$?([\d\s]+[,.]?\d*k?)\s*[-–]',
        r'(?:spot|спот|spot\s*price)[:\s]*\$?([\d\s]+[,.]?\d*k?)',
        r'(?:current|текущая|current\s*price)[:\s]*\$?([\d\s]+[,.]?\d*k?)',
        r'\@\s*\$?([\d\s]+[,.]?\d*k?)\s*(?:[-–]|$)',
        r'(?:level|уровень)\s*(?:1)?[:\s]*\$?([\d\s]+[,.]?\d*k?)',
        r'(?:avg|average|средн)[.a-z]*\s*(?:entry|price|вход)?[:\s]*\$?([\d\s]+[,.]?\d*k?)',
    ]
    tp_patterns = [
        r'(?:tp|take.profit|тейк|цель)\s*(?:\d\s*)?[:\s]+\$?([\d\s]+[,.]?\d*k?)',
        r'(?:targets?|цели)\s*[:\s]+\$?([\d\s]+[,.]?\d*k?)',
        r'(?:target)\s+([\d\s]+[,.]?\d*k?)',
    ]
    sl_patterns = [
        r'(?:sl|stop.loss|стоп|стоп.лосс|stoploss)[:\s]*\$?([\d\s]+[,.]?\d*k?)',
    ]

    for pat in entry_patterns:
        if entry_price:
            break
        p = _parse_price(text, pat)
        if p and _validate_price(p, asset) and not _price_in_million_context(text, p):
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

    dollar_prices = re.findall(r'\$([\d\s]+[,.]?\d*k?)', text)
    valid_prices = []
    for raw in dollar_prices:
        val = _normalize_price_token(raw)
        if val is not None and _validate_price(val, asset):
            valid_prices.append(val)

    if not entry_price and valid_prices:
        entry_price = valid_prices[0]
    if not take_profit and len(valid_prices) >= 2:
        take_profit = valid_prices[1]

    # DeFi/news filter: long text with news-like keywords but no TP/SL = not a signal
    if entry_price and not take_profit and not stop_loss:
        if len(text.strip()) >= MIN_TEXT_LEN_FOR_STRICT_SIGNAL and DEFI_NEWS_LIKE.search(text):
            return None

    confidence = 0.4
    if entry_price:
        confidence = 0.6
        if take_profit:
            confidence = 0.75
        if stop_loss:
            confidence = 0.85

    from app.services.sanitizer import sanitize_signal_text

    return ParsedSignal(
        asset=asset,
        direction=direction,
        entry_price=entry_price,
        take_profit=take_profit,
        stop_loss=stop_loss,
        confidence=confidence,
        original_text=sanitize_signal_text(text[:500]),
        entry_zone_low=entry_zone_low,
        entry_zone_high=entry_zone_high,
    )


async def collect_signals_from_channel(
    username: str, limit: Optional[int] = None
) -> ChannelScrapeResult:
    """Fetch and extract signals from a public Telegram channel."""
    from app.services.ocr_signal_parser import parse_signal_from_image_url

    lim = limit if limit is not None else 20
    posts = await fetch_channel_posts(username, limit=lim)
    signals = []
    ocr_enabled = os.getenv("OCR_TELEGRAM_ENABLED", "true").lower() in ("1", "true", "yes")
    ocr_max_images = int(os.getenv("OCR_TELEGRAM_MAX_IMAGES_PER_POST", "1"))
    ocr_sleep_ms = int(os.getenv("OCR_TELEGRAM_SLEEP_MS", "250"))

    for post in posts:
        sig = parse_signal_from_text(post.text) if post.text else None
        if sig:
            sig.timestamp = post.date
            sig.telegram_message_id = post.message_id
            signals.append(sig)
            continue

        # OCR fallback: only if enabled and message has images
        if ocr_enabled and post.image_urls:
            for u in post.image_urls[: max(0, ocr_max_images)]:
                try:
                    ocr_sig = await parse_signal_from_image_url(u)
                except Exception as e:
                    logger.debug("OCR error @%s msg=%s: %s", username, post.message_id, e)
                    ocr_sig = None
                if ocr_sig and ocr_sig.entry_price:
                    ocr_sig.timestamp = post.date
                    ocr_sig.telegram_message_id = post.message_id
                    # Make sure we store something traceable; keep original text empty if none
                    if not ocr_sig.original_text:
                        ocr_sig.original_text = f"[OCR] {u}"
                    signals.append(ocr_sig)
                    break
                # small throttle between OCR calls
                if ocr_sleep_ms > 0:
                    import asyncio as _aio
                    await _aio.sleep(ocr_sleep_ms / 1000.0)
    logger.info(f"@{username}: {len(posts)} posts, {len(signals)} signals")
    return ChannelScrapeResult(posts_fetched=len(posts), signals=signals, posts=posts)
