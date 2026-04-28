"""
OCR signal parser — extract trading signals from images.
Uses easyocr for text recognition, then runs signal parser on extracted text.
"""
import logging
import io
import httpx
import os
import time
import asyncio
import ipaddress
import socket
from collections import OrderedDict
from dataclasses import dataclass
from typing import Optional, Dict, List, Any
from urllib.parse import urlparse
from app.services.telegram_scraper import ParsedSignal, parse_signal_from_text

logger = logging.getLogger(__name__)

_reader = None


def _get_reader():
    """Lazy-load easyocr reader (heavy import)."""
    global _reader
    # Cache failure to avoid spamming logs
    if _reader is False:
        return None
    if _reader is None:
        try:
            import easyocr
            langs = os.getenv("OCR_LANGS", "en,ru")
            lang_list = [x.strip() for x in langs.split(",") if x.strip()]
            _reader = easyocr.Reader(lang_list or ["en"], gpu=False, verbose=False)
            logger.info("EasyOCR reader initialized")
        except Exception as e:
            logger.error(f"Failed to init EasyOCR: {e}")
            _reader = False
    return _reader


def _preprocess_enabled() -> bool:
    return os.getenv("OCR_PREPROCESS", "true").lower() in ("1", "true", "yes")


def _preprocess_scale() -> float:
    try:
        return float(os.getenv("OCR_PREPROCESS_SCALE", "2.0"))
    except ValueError:
        return 2.0


def _preprocess_max_variants() -> int:
    return int(os.getenv("OCR_PREPROCESS_MAX_VARIANTS", "6"))


def _debug_preprocess() -> bool:
    return os.getenv("OCR_DEBUG_PREPROCESS", "").lower() in ("1", "true", "yes")


def _make_image_variants(image_bytes: bytes) -> List[Any]:
    """
    Return a list of images acceptable by easyocr (numpy arrays).
    Includes original + preprocessed variants.
    """
    try:
        import numpy as np
        import cv2
    except Exception as e:
        logger.debug("OCR preprocess deps not available: %s", e)
        return [image_bytes]

    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return [image_bytes]

    variants: List[Any] = [img]
    if not _preprocess_enabled():
        return variants

    scale = max(1.0, _preprocess_scale())
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if scale != 1.0:
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    gray_blur = cv2.GaussianBlur(gray, (3, 3), 0)

    # Variant 1: CLAHE (boost local contrast), good for low-contrast screenshots
    try:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray_clahe = clahe.apply(gray)
    except Exception:
        gray_clahe = gray
    variants.append(gray_clahe)

    # Variant 2: Otsu threshold (global), often better for clean UI text
    try:
        _, otsu = cv2.threshold(gray_clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        variants.append(otsu)
        variants.append(cv2.bitwise_not(otsu))
    except Exception:
        pass

    # Variant 3: adaptive threshold
    thr = cv2.adaptiveThreshold(
        gray_blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        9,
    )
    variants.append(thr)
    variants.append(cv2.bitwise_not(thr))

    # Variant 4: light sharpen (unsharp mask) then threshold
    try:
        blur = cv2.GaussianBlur(gray_clahe, (0, 0), 1.0)
        sharp = cv2.addWeighted(gray_clahe, 1.6, blur, -0.6, 0)
        _, sharp_otsu = cv2.threshold(sharp, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        variants.append(sharp_otsu)
    except Exception:
        pass

    # Cap variants to avoid runaway CPU
    return variants[: max(1, _preprocess_max_variants())]


def _score_ocr_text(text: str, avg_conf: float) -> float:
    if not text:
        return 0.0
    t = text.strip()
    alnum = sum(1 for ch in t if ch.isalnum())
    density = alnum / max(1, len(t))
    return (avg_conf * 2.0) + (min(len(t), 400) / 100.0) + density


def extract_text_from_image(image_bytes: bytes) -> str:
    """Extract text from image bytes using EasyOCR (with optional preprocessing)."""
    reader = _get_reader()
    if not reader:
        return ""

    try:
        best_text = ""
        best_score = 0.0
        best_meta = None
        idx = 0
        for img in _make_image_variants(image_bytes):
            idx += 1
            try:
                results = reader.readtext(img, detail=1, paragraph=True)
            except TypeError:
                results = reader.readtext(img, detail=1)
            texts: List[str] = []
            confs: List[float] = []
            for r in results or []:
                if isinstance(r, (list, tuple)) and len(r) >= 3:
                    txt = str(r[1] or "").strip()
                    if txt:
                        texts.append(txt)
                        try:
                            confs.append(float(r[2]))
                        except Exception:
                            pass
            text = " ".join(texts).strip()
            avg_conf = (sum(confs) / len(confs)) if confs else 0.0
            score = _score_ocr_text(text, avg_conf)
            if score > best_score:
                best_score = score
                best_text = text
                best_meta = (idx, avg_conf, len(text))

        if _debug_preprocess():
            logger.info("OCR best_variant=%s score=%.3f avg_conf=%.3f len=%s",
                        best_meta[0] if best_meta else None,
                        best_score,
                        best_meta[1] if best_meta else 0.0,
                        best_meta[2] if best_meta else 0)
        logger.info(f"OCR extracted {len(best_text)} chars from image")
        return best_text
    except Exception as e:
        logger.error(f"OCR error: {e}")
        return ""

def _min_chars() -> int:
    return int(os.getenv("OCR_MIN_CHARS", "25"))


def _looks_like_useful_text(text: str) -> bool:
    """
    Fast filter to skip low-signal OCR outputs (charts/noise).
    Heuristics:
    - minimum length
    - enough alphanumeric chars (avoid mostly punctuation)
    """
    t = (text or "").strip()
    if len(t) < _min_chars():
        return False
    alnum = sum(1 for ch in t if ch.isalnum())
    return alnum / max(1, len(t)) >= 0.25


@dataclass(frozen=True)
class _CacheEntry:
    ts: float
    text: str


_cache_lock = asyncio.Lock()
_url_text_cache: "OrderedDict[str, _CacheEntry]" = OrderedDict()
_inflight_lock = asyncio.Lock()
_inflight: Dict[str, asyncio.Future] = {}
_http_client: Optional[httpx.AsyncClient] = None
_http_client_lock = asyncio.Lock()


def _cache_ttl_seconds() -> int:
    return int(os.getenv("OCR_CACHE_TTL_SECONDS", "86400"))  # 24h


def _cache_max_items() -> int:
    return int(os.getenv("OCR_CACHE_MAX_ITEMS", "2000"))


async def _cache_get(url: str) -> Optional[str]:
    ttl = _cache_ttl_seconds()
    now = time.time()
    async with _cache_lock:
        ent = _url_text_cache.get(url)
        if not ent:
            return None
        if ttl > 0 and (now - ent.ts) > ttl:
            _url_text_cache.pop(url, None)
            return None
        # LRU refresh
        _url_text_cache.move_to_end(url)
        return ent.text


async def _cache_set(url: str, text: str) -> None:
    now = time.time()
    max_items = _cache_max_items()
    async with _cache_lock:
        _url_text_cache[url] = _CacheEntry(ts=now, text=text)
        _url_text_cache.move_to_end(url)
        if max_items > 0:
            while len(_url_text_cache) > max_items:
                _url_text_cache.popitem(last=False)

async def _get_http_client() -> httpx.AsyncClient:
    global _http_client
    async with _http_client_lock:
        if _http_client is None or _http_client.is_closed:
            _http_client = httpx.AsyncClient(
                timeout=15,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (compatible; crypto-analytics/1.0)"},
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            )
        return _http_client


def _is_safe_public_image_url(image_url: str) -> bool:
    """Reject localhost/private-network URLs before OCR download.

    The OCR endpoint accepts user-controlled URLs. Without this guard it can be
    abused as SSRF against metadata services, localhost, Docker networks, etc.
    """
    try:
        parsed = urlparse(image_url)
        if parsed.scheme not in {"http", "https"}:
            return False
        host = parsed.hostname
        if not host:
            return False
        if host.lower() in {"localhost", "localhost.localdomain"}:
            return False

        addresses = {item[4][0] for item in socket.getaddrinfo(host, None)}
        if not addresses:
            return False
        for address in addresses:
            ip = ipaddress.ip_address(address)
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
                or ip.is_unspecified
            ):
                return False
        return True
    except Exception as e:
        logger.warning("OCR URL rejected by SSRF guard: %s (%s)", image_url, e)
        return False


async def _run_singleflight(image_url: str, coro):
    """
    Ensure only one OCR/download per URL concurrently.
    Others await the same Future.
    """
    async with _inflight_lock:
        fut = _inflight.get(image_url)
        if fut is not None:
            return await fut
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        _inflight[image_url] = fut
    try:
        res = await coro
        fut.set_result(res)
        return res
    except Exception as e:
        fut.set_exception(e)
        raise
    finally:
        async with _inflight_lock:
            _inflight.pop(image_url, None)

async def extract_text_from_url(image_url: str) -> str:
    """Download image and extract text."""
    if not _is_safe_public_image_url(image_url):
        logger.warning("OCR URL blocked by SSRF guard: %s", image_url)
        return ""

    cached = await _cache_get(image_url)
    if cached is not None:
        logger.debug("OCR cache hit for url=%s len=%s", image_url, len(cached))
        return cached

    async def _do():
        try:
            client = await _get_http_client()
            r = await client.get(image_url)
            if r.status_code == 200 and len(r.content) > 1000:
                text = extract_text_from_image(r.content)
                await _cache_set(image_url, text or "")
                return text
        except Exception as e:
            logger.error(f"Image download error: {e}")
        await _cache_set(image_url, "")
        return ""

    # singleflight avoids repeated downloads/OCR for same URL during a run
    return await _run_singleflight(image_url, _do())


def parse_signal_from_image(image_bytes: bytes) -> Optional[ParsedSignal]:
    """Extract text from image and parse trading signal."""
    text = extract_text_from_image(image_bytes)
    if not text:
        return None
    return parse_signal_from_text(text)


async def parse_signal_from_image_url(image_url: str) -> Optional[ParsedSignal]:
    """Download image, OCR it, parse signal."""
    text = await extract_text_from_url(image_url)
    if not text or not _looks_like_useful_text(text):
        return None
    return parse_signal_from_text(text)
