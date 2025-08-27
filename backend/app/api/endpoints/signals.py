from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from math import ceil
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.auth import get_current_active_user, require_admin, get_current_user
from app.services.signal_service import SignalService
from app.services.telegram_signal_service import TelegramSignalService
from app.models.user import User
from app.models.signal import Signal
from app import schemas
from app.schemas.signal import SignalResponse, SignalCreate, SignalUpdate, SignalFilterParams, SignalStats

router = APIRouter()


def get_channel_real_name(channel_id: int) -> str:
    """
    Возвращает реальное название канала по ID
    """
    channel_mapping = {
        200: "📱 Reddit",
        300: "🌐 External APIs", 
        301: "📊 CQS API",
        302: "📈 CTA API",
        400: "💬 Telegram",
        401: "🚀 CryptoPapa",
        402: "🐷 FatPigSignals", 
        403: "⚡ BinanceKiller",
        404: "🌍 CryptoSignalsWorld",
        405: "💎 CryptoPumps"
    }
    
    return channel_mapping.get(channel_id, f"📋 Unknown Source {channel_id}")


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


@router.get("/dashboard", response_model=List[dict])
def get_signals_dashboard(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get signals without JOIN - simple version for dashboard."""
    query = db.query(Signal)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    signals = query.order_by(Signal.created_at.desc()).offset(skip).limit(limit).all()
    
    # Convert to simple dict format
    result = []
    for signal in signals:
        signal_dict = {
            "id": signal.id,
            "asset": signal.asset,
            "symbol": signal.symbol,
            "direction": signal.direction,
            "entry_price": float(signal.entry_price) if signal.entry_price else None,
            "tp1_price": float(signal.tp1_price) if signal.tp1_price else None,
            "tp2_price": float(signal.tp2_price) if signal.tp2_price else None,
            "tp3_price": float(signal.tp3_price) if signal.tp3_price else None,
            "stop_loss": float(signal.stop_loss) if signal.stop_loss else None,
            "original_text": signal.original_text,
            "status": signal.status,
            "confidence_score": float(signal.confidence_score) if signal.confidence_score else None,
            "created_at": signal.created_at.isoformat() if signal.created_at else None,
            "updated_at": signal.updated_at.isoformat() if signal.updated_at else None,
            "expires_at": signal.expires_at.isoformat() if signal.expires_at else None,  # Ожидаемая дата выполнения
            "channel_id": signal.channel_id,
            "channel_name": get_channel_real_name(signal.channel_id)
        }
        result.append(signal_dict)
    
    return result


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

@router.get("/", response_model=List[SignalResponse])
def get_signals(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    channel_id: Optional[int] = None,
    asset: Optional[str] = None,
    direction: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get signals with filtering and pagination."""
    filters = SignalFilterParams(
        channel_id=channel_id,
        asset=asset,
        direction=direction,
        status=status,
        date_from=date_from,
        date_to=date_to
    )
    
    signal_service = SignalService(db)
    signals, total = signal_service.get_signals(
        skip=skip,
        limit=limit,
        filters=filters
    )
    
    return signals
