from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.signal import Signal
from app.models.channel import Channel

router = APIRouter()

@router.get("/signals", response_model=List[dict])
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
            "channel_id": signal.channel_id,
            "channel_name": f"Channel {signal.channel_id}" if signal.channel_id else "Unknown"
        }
        result.append(signal_dict)
    
    return result

@router.get("/channels", response_model=List[dict])
def get_channels_dashboard(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get channels without complex JOIN - simple version for dashboard."""
    query = db.query(Channel)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    channels = query.order_by(Channel.created_at.desc()).offset(skip).limit(limit).all()
    
    # Convert to simple dict format
    result = []
    for channel in channels:
        channel_dict = {
            "id": channel.id,
            "name": channel.name,
            "username": channel.username,
            "description": channel.description,
            "platform": channel.platform,
            "is_active": channel.is_active,
            "is_verified": channel.is_verified,
            "subscribers_count": channel.subscribers_count,
            "category": channel.category,
            "priority": channel.priority,
            "expected_accuracy": channel.expected_accuracy,
            "status": channel.status,
            "created_at": channel.created_at.isoformat() if channel.created_at else None,
            "updated_at": channel.updated_at.isoformat() if channel.updated_at else None
        }
        result.append(channel_dict)
    
    return result
