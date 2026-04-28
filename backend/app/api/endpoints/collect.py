"""
Signal collection endpoints — trigger real data collection from Telegram channels.
"""
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Any, Dict

from app.core.database import get_db
from app.core.auth import get_current_user, get_optional_current_user, require_premium
from app.models.channel import Channel
from app.models.signal import Signal
from app.models.user import User
from app.services.telegram_scraper import collect_signals_from_channel
from app.services.collection_pipeline import (
    persist_parsed_signals_for_channel,
    persist_shadow_telegram_posts_if_enabled,
    run_telethon_collect_all_channels,
    telegram_fetch_limit,
    telethon_collect_channel_core,
)
from app.core.config import get_settings
from app.services.reddit_scraper import collect_reddit_signals, CRYPTO_SUBREDDITS
from app.services.ocr_signal_parser import parse_signal_from_image_url
from app.services.deep_collector import deep_collect_and_validate
from app.services.telethon_collector import is_authenticated as telethon_ready
from app.services.metrics_calculator import recalculate_all_channels, recalculate_channel_metrics
from app.services.price_validator import validate_signal_price
from app.services.signal_checker import check_pending_signals
from app.services.historical_validator import validate_all_signals
from app.core.rate_limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/collect/{channel_id}")
async def collect_channel_signals(
    channel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Collect signals from a specific channel."""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    username = channel.username
    if not username:
        if channel.url:
            username = channel.url.rstrip("/").split("/")[-1]
        else:
            raise HTTPException(status_code=400, detail="Channel has no username or URL")

    settings = get_settings()
    lim = telegram_fetch_limit(channel, settings)
    scrape = await collect_signals_from_channel(username, limit=lim)
    persist_shadow_telegram_posts_if_enabled(db, channel, scrape.posts, web_username=username)
    st = persist_parsed_signals_for_channel(
        db,
        channel,
        scrape.signals,
        posts_fetched=scrape.posts_fetched,
        record_metrics=True,
    )
    new_count = st["saved"]

    if new_count > 0:
        db.commit()

    return {
        "channel": channel.name,
        "username": username,
        "posts_fetched": scrape.posts_fetched,
        "posts_parsed": len(scrape.signals),
        "new_signals_saved": new_count,
        "total_signals": channel.signals_count,
    }


@router.post("/collect-all")
async def collect_all_channels(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_premium),
):
    """Collect signals from all active channels."""
    settings = get_settings()
    channels = db.query(Channel).filter(
        Channel.is_active == True,
        Channel.platform == "telegram",
    ).all()

    results = []
    for channel in channels:
        username = channel.username
        if not username and channel.url:
            username = channel.url.rstrip("/").split("/")[-1]
        if not username:
            continue

        try:
            lim = telegram_fetch_limit(channel, settings)
            scrape = await collect_signals_from_channel(username, limit=lim)
            persist_shadow_telegram_posts_if_enabled(db, channel, scrape.posts, web_username=username)
            st = persist_parsed_signals_for_channel(
                db,
                channel,
                scrape.signals,
                posts_fetched=scrape.posts_fetched,
                record_metrics=True,
            )
            new_count = st["saved"]

            results.append({
                "channel": channel.name,
                "username": username,
                "posts_fetched": scrape.posts_fetched,
                "signals_found": len(scrape.signals),
                "new_saved": new_count,
            })
        except Exception as e:
            logger.error(f"Error collecting from {channel.name}: {e}")
            results.append({
                "channel": channel.name,
                "error": str(e),
            })

    db.commit()
    recalculate_all_channels(db)

    return {
        "channels_processed": len(results),
        "results": results,
    }


@router.post("/recalculate-metrics")
async def recalculate_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_premium),
):
    """Recalculate accuracy and ROI for all channels."""
    results = recalculate_all_channels(db)
    return {
        "channels_updated": len(results),
        "results": [r for r in results if r.get("total_signals", 0) > 0],
    }


@router.get("/validate-signal/{signal_id}")
async def validate_signal(
    signal_id: int,
    db: Session = Depends(get_db),
):
    """Validate a signal's price against current market data."""
    signal = db.query(Signal).filter(Signal.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    result = await validate_signal_price(signal.asset, float(signal.entry_price))
    return {
        "signal_id": signal.id,
        "asset": signal.asset,
        "entry_price": float(signal.entry_price),
        "validation": result,
    }


@router.post("/check-signals")
async def check_signals(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_premium),
):
    """Check pending signals against current market prices. Updates TP/SL hit status."""
    result = await check_pending_signals(db)
    return result


@router.post("/deep-collect")
@limiter.limit("5/hour")
async def deep_collect(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_premium),
):
    """Deep historical collection: scrape ALL posts, validate against CoinGecko prices."""
    result = await deep_collect_and_validate(db)
    return result


@router.post("/collect-reddit")
async def collect_reddit(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_premium),
):
    """Collect signals from Reddit crypto subreddits."""
    total_saved = 0
    results = []

    for sub in CRYPTO_SUBREDDITS:
        try:
            scrape = await collect_reddit_signals(sub, limit=25)
            channel = db.query(Channel).filter(Channel.username == f"r_{sub}").first()
            if not channel:
                channel = Channel(
                    username=f"r_{sub}", name=f"r/{sub}",
                    url=f"https://reddit.com/r/{sub}", platform="reddit",
                    description=f"Reddit r/{sub}", category="community",
                    is_active=True, status="active", signals_count=0,
                )
                db.add(channel)
                db.flush()

            st = persist_parsed_signals_for_channel(
                db,
                channel,
                scrape.signals,
                posts_fetched=scrape.posts_fetched,
                record_metrics=True,
            )
            saved = st["saved"]
            total_saved += saved
            if saved > 0:
                results.append({"subreddit": sub, "saved": saved})
        except Exception as e:
            logger.error(f"Reddit r/{sub}: {e}")

    db.commit()
    return {"subreddits_checked": len(CRYPTO_SUBREDDITS), "signals_saved": total_saved, "results": results}


@router.post("/ocr-parse")
async def ocr_parse_signal(
    image_url: str,
    current_user: User = Depends(require_premium),
):
    """Extract trading signal from image URL via OCR (premium-only).

    This endpoint downloads user-provided URLs, so it must not be public.
    `parse_signal_from_image_url` also blocks localhost/private network URLs.
    """
    sig = await parse_signal_from_image_url(image_url)
    if sig:
        return {
            "found": True,
            "asset": sig.asset,
            "direction": sig.direction,
            "entry_price": sig.entry_price,
            "take_profit": sig.take_profit,
            "stop_loss": sig.stop_loss,
            "confidence": sig.confidence,
        }
    return {"found": False, "message": "No signal detected in image"}


@router.post("/validate-history")
async def validate_historical(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_premium),
):
    """Validate all signals against historical CoinGecko prices. Updates accuracy."""
    result = await validate_all_signals(db)
    return result


@router.get("/telethon-status")
async def telethon_status():
    """Check if Telethon is authenticated."""
    return {
        "authenticated": telethon_ready(),
        "how_to_auth": "Run: cd backend && python -m app.services.telethon_collector --auth",
    }


@router.post("/telethon-collect/{channel_username}")
async def telethon_collect(
    channel_username: str,
    days: int = 90,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_premium),
):
    """Collect deep history from a channel via Telethon (requires auth).

    При `SHADOW_PIPELINE_ENABLED` и `SHADOW_TELETHON_FULL_MTPROTO` в shadow пишется
    `raw_payload.mtproto` — JSON-safe снимок TL (Message/MessageService).
    """
    if not telethon_ready():
        return {"error": "Telethon not authenticated", "how_to": "Run: python -m app.services.telethon_collector --auth"}

    channel = db.query(Channel).filter(Channel.username == channel_username).first()
    if not channel:
        return {"error": f"Channel @{channel_username} not in database"}

    body = await telethon_collect_channel_core(db, channel, days)
    if body.get("error"):
        return body
    db.commit()
    return {
        "channel": body["channel"],
        "signals_found": body["signals_found"],
        "new_saved": body["new_saved"],
        "total": body["total"],
        "shadow_raw": body["shadow_raw"],
    }


@router.post("/telethon-collect-all")
async def telethon_collect_all(
    days: int = 90,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_premium),
):
    """Telethon deep collect для всех активных Telegram-каналов из БД (как /collect-all по охвату)."""
    if not telethon_ready():
        return {
            "error": "Telethon not authenticated",
            "how_to": "Run: python -m app.services.telethon_collector --auth",
        }

    batch = await run_telethon_collect_all_channels(db, days)
    db.commit()
    recalculate_all_channels(db)
    return batch


@router.get("/bot-status")
async def bot_status(db: Session = Depends(get_db)):
    """Check Telegram bot status and channel access."""
    from app.services.telegram_bot import check_bot_access_to_channels
    channels = db.query(Channel).filter(Channel.platform == "telegram").all()
    usernames = [ch.username for ch in channels if ch.username]
    result = await check_bot_access_to_channels(usernames)
    return result
