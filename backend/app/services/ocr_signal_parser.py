"""
OCR signal parser — extract trading signals from images.
Uses easyocr for text recognition, then runs signal parser on extracted text.
"""
import logging
import io
import httpx
from typing import Optional
from app.services.telegram_scraper import ParsedSignal, parse_signal_from_text

logger = logging.getLogger(__name__)

_reader = None


def _get_reader():
    """Lazy-load easyocr reader (heavy import)."""
    global _reader
    if _reader is None:
        try:
            import easyocr
            _reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            logger.info("EasyOCR reader initialized")
        except Exception as e:
            logger.error(f"Failed to init EasyOCR: {e}")
    return _reader


def extract_text_from_image(image_bytes: bytes) -> str:
    """Extract text from image bytes using EasyOCR."""
    reader = _get_reader()
    if not reader:
        return ""

    try:
        results = reader.readtext(image_bytes, detail=0)
        text = " ".join(results)
        logger.info(f"OCR extracted {len(text)} chars from image")
        return text
    except Exception as e:
        logger.error(f"OCR error: {e}")
        return ""


async def extract_text_from_url(image_url: str) -> str:
    """Download image and extract text."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(image_url)
            if r.status_code == 200 and len(r.content) > 1000:
                return extract_text_from_image(r.content)
    except Exception as e:
        logger.error(f"Image download error: {e}")
    return ""


def parse_signal_from_image(image_bytes: bytes) -> Optional[ParsedSignal]:
    """Extract text from image and parse trading signal."""
    text = extract_text_from_image(image_bytes)
    if not text:
        return None
    return parse_signal_from_text(text)


async def parse_signal_from_image_url(image_url: str) -> Optional[ParsedSignal]:
    """Download image, OCR it, parse signal."""
    text = await extract_text_from_url(image_url)
    if not text:
        return None
    return parse_signal_from_text(text)
