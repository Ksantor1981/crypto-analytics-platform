from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from math import ceil

from app.core.database import get_db
from app.core.auth import get_current_active_user, require_admin
from app.services.signal_service import SignalService
from app.services.telegram_signal_service import TelegramSignalService
from app.models.user import User
from app import schemas

router = APIRouter()


@router.post("/", response_model=schemas.signal.SignalResponse, status_code=status.HTTP_201_CREATED)
def create_signal(
    signal_in: schemas.signal.SignalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new signal."""
    signal_service = SignalService(db)
    # TODO: Add logic to check if user has permission to create signal for the channel
    return signal_service.create_signal(signal_in=signal_in)


@router.get("/", response_model=schemas.signal.SignalListResponse)
def get_signals(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    filters: schemas.signal.SignalFilterParams = Depends(),
):
    """Retrieve a list of signals with pagination and filtering."""
    signal_service = SignalService(db)
    signals, total = signal_service.get_signals(
        skip=skip, limit=limit, filters=filters
    )
    
    pages = ceil(total / limit) if limit > 0 else 0
    page = (skip // limit) + 1

    return {
        "signals": signals,
        "total": total,
        "page": page,
        "size": len(signals),
        "pages": pages,
    }


@router.get("/{signal_id}", response_model=schemas.signal.SignalWithChannel)
def get_signal(
    signal_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve a specific signal by its ID."""
    signal_service = SignalService(db)
    signal = signal_service.get_signal_by_id(signal_id)
    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Signal not found"
        )
    return signal


@router.put("/{signal_id}", response_model=schemas.signal.SignalResponse, dependencies=[Depends(require_admin)])
def update_signal(
    signal_id: int,
    signal_in: schemas.signal.SignalUpdate,
    db: Session = Depends(get_db),
):
    """Update a signal's details (admin only)."""
    signal_service = SignalService(db)
    updated_signal = signal_service.update_signal(signal_id=signal_id, signal_in=signal_in)
    if not updated_signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Signal not found"
        )
    return updated_signal


@router.delete("/{signal_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def delete_signal(
    signal_id: int,
    db: Session = Depends(get_db),
):
    """Delete a signal (admin only)."""
    signal_service = SignalService(db)
    if not signal_service.delete_signal(signal_id=signal_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Signal not found"
        )
    return


@router.get("/stats/overview", response_model=schemas.signal.SignalStats, dependencies=[Depends(require_admin)])
def get_general_stats(db: Session = Depends(get_db)):
    """Get overall signal statistics."""
    signal_service = SignalService(db)
    return signal_service.get_signal_stats()


@router.get("/stats/channel/{channel_id}", response_model=schemas.signal.ChannelSignalStats)
def get_channel_stats(
    channel_id: int,
    db: Session = Depends(get_db),
):
    """Get signal statistics for a specific channel."""
    signal_service = SignalService(db)
    stats = signal_service.get_channel_stats(channel_id=channel_id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found or no signals for this channel"
        )
    return stats


@router.get("/stats/asset-performance", response_model=List[schemas.signal.AssetPerformance], dependencies=[Depends(require_admin)])
def get_asset_performance(
    db: Session = Depends(get_db),
):
    """Get performance statistics for each asset."""
    signal_service = SignalService(db)
    return signal_service.get_asset_performance()


@router.post("/telegram/webhook", response_model=schemas.signal.TelegramSignalResponse)
def handle_telegram_signal(
    signal_in: schemas.signal.TelegramSignalCreate,
    db: Session = Depends(get_db)
    # TODO: Add API Key security
):
    """Webhook endpoint to receive signals from Telegram bots/integrations."""
    telegram_signal_service = TelegramSignalService(db)
    # This is a simplified version. A real implementation would need more logic
    # to parse different message formats, find channels, etc.
    telegram_signal = telegram_signal_service.create_signal(signal_in)
    return telegram_signal
