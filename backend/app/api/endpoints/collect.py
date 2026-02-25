"""
Signal collection endpoints — trigger real data collection from Telegram channels.
"""
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.auth import get_current_user, get_optional_current_user
from app.models.channel import Channel
from app.models.signal import Signal
from app.models.user import User
from app.services.telegram_scraper import collect_signals_from_channel
from app.services.metrics_calculator import recalculate_all_channels, recalculate_channel_metrics

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

    signals = await collect_signals_from_channel(username)

    new_count = 0
    for sig in signals:
        if not sig.entry_price:
            continue

        existing = db.query(Signal).filter(
            Signal.channel_id == channel.id,
            Signal.original_text == sig.original_text[:500],
        ).first()
        if existing:
            continue

        db_signal = Signal(
            channel_id=channel.id,
            asset=sig.asset,
            symbol=sig.asset.replace("/", ""),
            direction=sig.direction,
            entry_price=sig.entry_price,
            tp1_price=sig.take_profit,
            stop_loss=sig.stop_loss,
            confidence_score=sig.confidence,
            original_text=sig.original_text,
            status="PENDING",
        )
        db.add(db_signal)
        new_count += 1

    if new_count > 0:
        channel.signals_count = (channel.signals_count or 0) + new_count
        db.commit()

    return {
        "channel": channel.name,
        "username": username,
        "posts_parsed": len(signals),
        "new_signals_saved": new_count,
        "total_signals": channel.signals_count,
    }


@router.post("/collect-all")
async def collect_all_channels(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Collect signals from all active channels."""
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
            signals = await collect_signals_from_channel(username)
            new_count = 0
            for sig in signals:
                if not sig.entry_price:
                    continue

                existing = db.query(Signal).filter(
                    Signal.channel_id == channel.id,
                    Signal.original_text == sig.original_text[:500],
                ).first()
                if existing:
                    continue

                db_signal = Signal(
                    channel_id=channel.id,
                    asset=sig.asset,
                    symbol=sig.asset.replace("/", ""),
                    direction=sig.direction,
                    entry_price=sig.entry_price,
                    tp1_price=sig.take_profit,
                    stop_loss=sig.stop_loss,
                    confidence_score=sig.confidence,
                    original_text=sig.original_text,
                    status="PENDING",
                )
                db.add(db_signal)
                new_count += 1

            if new_count > 0:
                channel.signals_count = (channel.signals_count or 0) + new_count

            results.append({
                "channel": channel.name,
                "username": username,
                "signals_found": len(signals),
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
    current_user: User = Depends(get_current_user),
):
    """Recalculate accuracy and ROI for all channels."""
    results = recalculate_all_channels(db)
    return {
        "channels_updated": len(results),
        "results": [r for r in results if r.get("total_signals", 0) > 0],
    }
