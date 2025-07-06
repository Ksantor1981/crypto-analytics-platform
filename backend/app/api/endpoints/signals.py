"""
API endpoints for signal management
"""
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Request
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from math import ceil
from decimal import Decimal
from datetime import datetime, timezone
import logging

from app.core.database import get_db
from app.core.auth import (
    get_current_active_user,
    get_optional_current_user,
    require_admin,
    require_premium
)
from app.services.signal_service import SignalService
from app.schemas.signal import (
    SignalCreate,
    SignalUpdate,
    SignalResponse,
    SignalWithChannel,
    SignalListResponse,
    SignalFilterParams,
    SignalStats,
    ChannelSignalStats,
    AssetPerformance,
    TopSignal,
    SignalDirection,
    SignalStatus,
    TelegramSignalCreate,
    TelegramSignalResponse
)
from app.models.user import User
from app.core.logging import get_logger
from app.models.signal import TelegramSignal
from pydantic import BaseModel, Field

# Настройка логирования
logger = get_logger(__name__)

router = APIRouter()

def convert_signal_to_response(signal) -> SignalWithChannel:
    """Convert Signal model to SignalWithChannel response."""
    return SignalWithChannel(
        id=signal.id,
        channel_id=signal.channel_id,
        asset=signal.asset,
        direction=signal.direction,
        entry_price=float(signal.entry_price),
        tp1_price=float(signal.tp1_price) if signal.tp1_price else None,
        tp2_price=float(signal.tp2_price) if signal.tp2_price else None,
        tp3_price=float(signal.tp3_price) if signal.tp3_price else None,
        stop_loss=float(signal.stop_loss) if signal.stop_loss else None,
        entry_price_low=float(signal.entry_price_low) if signal.entry_price_low else None,
        entry_price_high=float(signal.entry_price_high) if signal.entry_price_high else None,
        original_text=signal.original_text,
        status=signal.status,
        message_timestamp=signal.message_timestamp,
        telegram_message_id=signal.telegram_message_id,
        entry_hit_at=signal.entry_hit_at,
        tp1_hit_at=signal.tp1_hit_at,
        tp2_hit_at=signal.tp2_hit_at,
        tp3_hit_at=signal.tp3_hit_at,
        sl_hit_at=signal.sl_hit_at,
        final_exit_price=float(signal.final_exit_price) if signal.final_exit_price else None,
        final_exit_timestamp=signal.final_exit_timestamp,
        profit_loss_percentage=float(signal.profit_loss_percentage) if signal.profit_loss_percentage else None,
        profit_loss_absolute=float(signal.profit_loss_absolute) if signal.profit_loss_absolute else None,
        is_successful=signal.is_successful,
        reached_tp1=signal.reached_tp1,
        reached_tp2=signal.reached_tp2,
        reached_tp3=signal.reached_tp3,
        hit_stop_loss=signal.hit_stop_loss,
        ml_success_probability=float(signal.ml_success_probability) if signal.ml_success_probability else None,
        ml_predicted_roi=float(signal.ml_predicted_roi) if signal.ml_predicted_roi else None,
        is_ml_prediction_correct=signal.is_ml_prediction_correct,
        confidence_score=float(signal.confidence_score) if signal.confidence_score else None,
        risk_reward_ratio=float(signal.risk_reward_ratio) if signal.risk_reward_ratio else None,
        expires_at=signal.expires_at,
        cancelled_at=signal.cancelled_at,
        cancellation_reason=signal.cancellation_reason,
        created_at=signal.created_at,
        updated_at=signal.updated_at,
        channel_name=signal.channel.name if signal.channel else None,
        channel_username=signal.channel.url if signal.channel else None
    )

@router.get("/", response_model=SignalListResponse)
async def get_signals(
    skip: int = Query(0, ge=0, description="Number of signals to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of signals to return"),
    channel_id: Optional[int] = Query(None, description="Filter by channel ID"),
    asset: Optional[str] = Query(None, description="Filter by asset (e.g., BTC/USDT)"),
    direction: Optional[SignalDirection] = Query(None, description="Filter by signal direction"),
    status: Optional[SignalStatus] = Query(None, description="Filter by signal status"),
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    successful_only: Optional[bool] = Query(None, description="Show only successful signals"),
    min_roi: Optional[float] = Query(None, description="Minimum ROI percentage"),
    max_roi: Optional[float] = Query(None, description="Maximum ROI percentage"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Get signals with filtering and pagination."""
    signal_service = SignalService(db)
    
    # Parse date filters
    date_from_parsed = None
    date_to_parsed = None
    if date_from:
        try:
            from datetime import datetime
            date_from_parsed = datetime.fromisoformat(date_from)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_from format. Use YYYY-MM-DD")
    
    if date_to:
        try:
            from datetime import datetime
            date_to_parsed = datetime.fromisoformat(date_to)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_to format. Use YYYY-MM-DD")
    
    # Create filter params
    filters = SignalFilterParams(
        channel_id=channel_id,
        asset=asset,
        direction=direction,
        status=status,
        date_from=date_from_parsed,
        date_to=date_to_parsed,
        successful_only=successful_only,
        min_roi=min_roi,
        max_roi=max_roi
    )
    
    # Determine user subscription tier
    user_tier = current_user.role if current_user else "FREE_USER"
    
    # Get signals
    signals, total = signal_service.get_signals(
        skip=skip, 
        limit=limit, 
        filters=filters,
        user_subscription_tier=user_tier
    )
    
    # Calculate pagination
    pages = ceil(total / limit) if total > 0 else 0
    page = (skip // limit) + 1
    
    # Convert to response format
    signal_responses = [convert_signal_to_response(signal) for signal in signals]
    
    return SignalListResponse(
        signals=signal_responses,
        total=total,
        page=page,
        size=limit,
        pages=pages
    )

@router.get("/{signal_id}", response_model=SignalWithChannel)
async def get_signal(
    signal_id: int,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific signal by ID."""
    signal_service = SignalService(db)
    
    signal = signal_service.get_signal_by_id(signal_id)
    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signal not found"
        )
    
    return convert_signal_to_response(signal)

@router.post("/", response_model=SignalResponse, dependencies=[Depends(require_admin)])
async def create_signal(
    signal_data: SignalCreate,
    db: Session = Depends(get_db)
):
    """Create a new signal (admin only)."""
    signal_service = SignalService(db)
    
    signal = signal_service.create_signal(signal_data)
    
    return SignalResponse.from_orm(signal)

@router.put("/{signal_id}", response_model=SignalResponse, dependencies=[Depends(require_admin)])
async def update_signal(
    signal_id: int,
    signal_data: SignalUpdate,
    db: Session = Depends(get_db)
):
    """Update signal information (admin only)."""
    signal_service = SignalService(db)
    
    signal = signal_service.update_signal(signal_id, signal_data)
    
    return SignalResponse.from_orm(signal)

@router.delete("/{signal_id}", dependencies=[Depends(require_admin)])
async def delete_signal(
    signal_id: int,
    db: Session = Depends(get_db)
):
    """Delete signal (admin only)."""
    signal_service = SignalService(db)
    
    success = signal_service.delete_signal(signal_id)
    
    if success:
        return {"message": "Signal deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete signal"
        )

@router.post("/{signal_id}/cancel", response_model=SignalResponse, dependencies=[Depends(require_admin)])
async def cancel_signal(
    signal_id: int,
    reason: str = Query("Manual cancellation", description="Cancellation reason"),
    db: Session = Depends(get_db)
):
    """Cancel a pending signal (admin only)."""
    signal_service = SignalService(db)
    
    signal = signal_service.cancel_signal(signal_id, reason)
    
    return SignalResponse.from_orm(signal)

@router.get("/stats/overview", response_model=SignalStats)
async def get_signal_stats(
    channel_id: Optional[int] = Query(None, description="Filter by channel ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get signal statistics overview."""
    signal_service = SignalService(db)
    
    # Create filters
    from datetime import datetime, timedelta
    date_from = datetime.utcnow() - timedelta(days=days)
    
    filters = SignalFilterParams(
        channel_id=channel_id,
        date_from=date_from
    )
    
    stats = signal_service.get_signal_stats(filters)
    
    return stats

@router.get("/stats/channel/{channel_id}", response_model=ChannelSignalStats)
async def get_channel_signal_stats(
    channel_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get signal statistics for a specific channel."""
    signal_service = SignalService(db)
    
    stats = signal_service.get_channel_stats(channel_id, days)
    
    return stats

@router.get("/analytics/top-performing", response_model=List[TopSignal])
async def get_top_performing_signals(
    limit: int = Query(10, ge=1, le=50, description="Number of top signals to return"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get top performing signals by ROI."""
    signal_service = SignalService(db)
    
    signals = signal_service.get_top_performing_signals(limit, days)
    
    # Convert to TopSignal format
    top_signals = []
    for signal in signals:
        top_signals.append(TopSignal(
            id=signal.id,
            asset=signal.asset,
            direction=signal.direction,
            entry_price=float(signal.entry_price),
            final_exit_price=float(signal.final_exit_price) if signal.final_exit_price else None,
            profit_loss_percentage=float(signal.profit_loss_percentage) if signal.profit_loss_percentage else None,
            status=signal.status,
            channel_name=signal.channel.name if signal.channel else None,
            message_timestamp=signal.message_timestamp,
            best_target_hit=signal.best_target_hit
        ))
    
    return top_signals

@router.get("/analytics/asset-performance", response_model=List[AssetPerformance])
async def get_asset_performance(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get performance analytics by asset."""
    signal_service = SignalService(db)
    
    performance = signal_service.get_asset_performance(days)
    
    return performance

@router.post("/maintenance/expire-old", dependencies=[Depends(require_admin)])
async def expire_old_signals(db: Session = Depends(get_db)):
    """Expire signals that have passed their expiration time (admin only)."""
    signal_service = SignalService(db)
    
    expired_count = signal_service.expire_old_signals()
    
    return {"message": f"Expired {expired_count} signals"}

# Premium endpoints
@router.get("/premium/advanced-analytics", dependencies=[Depends(require_premium)])
async def get_advanced_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(require_premium),
    db: Session = Depends(get_db)
):
    """Get advanced analytics (premium only)."""
    signal_service = SignalService(db)
    
    # Get comprehensive analytics
    stats = signal_service.get_signal_stats()
    asset_performance = signal_service.get_asset_performance(days)
    top_signals = signal_service.get_top_performing_signals(20, days)
    
    return {
        "overview": stats,
        "asset_performance": asset_performance,
        "top_signals": [
            {
                "id": s.id,
                "asset": s.asset,
                "roi": float(s.profit_loss_percentage) if s.profit_loss_percentage else 0,
                "channel": s.channel.name if s.channel else None
            }
            for s in top_signals
        ],
        "insights": {
            "best_performing_asset": asset_performance[0].asset if asset_performance else None,
            "most_active_asset": max(asset_performance, key=lambda x: x.total_signals).asset if asset_performance else None,
            "avg_signal_duration": stats.average_duration_hours,
            "success_rate_trend": "stable"  # Placeholder for trend analysis
        }
    }

# Telegram signal endpoints (simplified for integration)
@router.post("/telegram/", response_model=TelegramSignalResponse)
async def create_telegram_signal(
    signal: TelegramSignalCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new Telegram signal."""
    try:
        db_signal = TelegramSignal(
            symbol=signal.symbol.upper(),
            signal_type=signal.signal_type.lower(),
            entry_price=signal.entry_price,
            target_price=signal.target_price,
            stop_loss=signal.stop_loss,
            confidence=signal.confidence,
            source=signal.source,
            original_text=signal.original_text,
            metadata=signal.metadata,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_signal)
        db.commit()
        db.refresh(db_signal)
        
        # Convert to response
        response = TelegramSignalResponse(
            id=db_signal.id,
            symbol=db_signal.symbol,
            signal_type=db_signal.signal_type,
            entry_price=float(db_signal.entry_price) if db_signal.entry_price else None,
            target_price=float(db_signal.target_price) if db_signal.target_price else None,
            stop_loss=float(db_signal.stop_loss) if db_signal.stop_loss else None,
            confidence=float(db_signal.confidence),
            source=db_signal.source,
            status=db_signal.status,
            created_at=db_signal.created_at,
            metadata=db_signal.metadata
        )
        
        # Schedule background processing
        background_tasks.add_task(process_signal_background, db_signal.id)
        
        return response
        
    except Exception as e:
        logger.error(f"Error creating telegram signal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create signal"
        )

@router.get("/telegram/", response_model=List[TelegramSignalResponse])
async def get_telegram_signals(
    skip: int = 0,
    limit: int = 100,
    symbol: Optional[str] = None,
    signal_type: Optional[str] = None,
    source: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get Telegram signals."""
    query = db.query(TelegramSignal)
    
    if symbol:
        query = query.filter(TelegramSignal.symbol.ilike(f"%{symbol.upper()}%"))
    
    if signal_type:
        query = query.filter(TelegramSignal.signal_type == signal_type.lower())
    
    if source:
        query = query.filter(TelegramSignal.source.ilike(f"%{source}%"))
    
    signals = query.offset(skip).limit(limit).all()
    
    return [
        TelegramSignalResponse(
            id=signal.id,
            symbol=signal.symbol,
            signal_type=signal.signal_type,
            entry_price=float(signal.entry_price) if signal.entry_price else None,
            target_price=float(signal.target_price) if signal.target_price else None,
            stop_loss=float(signal.stop_loss) if signal.stop_loss else None,
            confidence=float(signal.confidence),
            source=signal.source,
            status=signal.status,
            created_at=signal.created_at,
            metadata=signal.metadata
        ) for signal in signals
    ]

@router.post("/telegram/batch", response_model=Dict)
async def create_telegram_signals_batch(
    signals: List[TelegramSignalCreate],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create multiple Telegram signals in batch."""
    try:
        created_signals = []
        
        for signal_data in signals:
            db_signal = TelegramSignal(
                symbol=signal_data.symbol.upper(),
                signal_type=signal_data.signal_type.lower(),
                entry_price=signal_data.entry_price,
                target_price=signal_data.target_price,
                stop_loss=signal_data.stop_loss,
                confidence=signal_data.confidence,
                source=signal_data.source,
                original_text=signal_data.original_text,
                metadata=signal_data.metadata,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            created_signals.append(db_signal)
        
        db.add_all(created_signals)
        db.commit()
        
        # Schedule background processing for all signals
        for signal in created_signals:
            background_tasks.add_task(process_signal_background, signal.id)
        
        return {
            "success": True,
            "message": f"Created {len(created_signals)} signals",
            "signal_ids": [signal.id for signal in created_signals]
        }
        
    except Exception as e:
        logger.error(f"Error creating signals batch: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create signals batch"
        )

@router.get("/telegram/health")
async def telegram_signals_health():
    """Health check for Telegram signals endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "telegram-signals"
    }

async def process_signal_background(signal_id: int):
    """Background task to process the signal."""
    try:
        logger.info(f"Processing signal {signal_id} in background")
        # Add any background processing logic here
        # For example: ML analysis, validation, notifications, etc.
        
    except Exception as e:
        logger.error(f"Error processing signal {signal_id}: {e}")

# Health check для сигналов
@router.get("/signals/health")
async def signals_health():
    """
    Проверка здоровья сервиса сигналов
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_signals": len(signals_storage),
        "active_signals": len([s for s in signals_storage if s["status"] == "active"]),
        "service": "telegram_signals"
    } 