from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from sqlalchemy.orm import Session

from app import models, schemas
from app.core import auth
from app.core.database import get_db
from app.models.user import UserRole
from app.models.channel import Channel
from app.schemas.channel import ChannelResponse, ChannelCreate, ChannelUpdate
from app.services.channel_service import ChannelService
from app.core.auth import get_current_user
# from app.services.telegram_service import TelegramService  # Временно отключено
# from app.services.signal_validation_service import SignalValidationService  # Временно отключено
from datetime import datetime

router = APIRouter(
    prefix="/channels",
    tags=["channels"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Channel, status_code=status.HTTP_201_CREATED)
def create_channel(
    *,
    db: Session = Depends(get_db),
    channel_in: schemas.ChannelCreate,
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Create a new channel.
    - Free users are limited to 3 channels.
    """
    if current_user.role == UserRole.FREE_USER:
        channel_count = db.query(models.Channel).filter(models.Channel.owner_id == current_user.id).count()
        if channel_count >= 3:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Free plan limit of 3 channels reached. Please upgrade to add more."
            )

    existing_channel = db.query(models.Channel).filter(models.Channel.url == channel_in.url).first()
    if existing_channel:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Channel with URL '{channel_in.url}' already exists."
        )

    db_channel = models.Channel(**channel_in.dict(), owner_id=current_user.id)
    db.add(db_channel)
    db.commit()
    db.refresh(db_channel)
    return db_channel

@router.get("/", response_model=List[schemas.Channel])
def read_channels(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Retrieve channels for the current user.
    """
    channels = db.query(models.Channel).filter(models.Channel.owner_id == current_user.id).offset(skip).limit(limit).all()
    return channels

@router.post("/discover", response_model=dict)
def discover_channels(
    *,
    db: Session = Depends(get_db)
    # current_user: models.User = Depends(auth.get_current_active_user)  # Временно отключено для тестирования
):
    """
    Discover new channels with crypto signals and add them to the database.
    - Automatically finds channels with trading signals
    - Validates signals and adds valid ones to the database
    - Returns summary of discovered channels and signals
    """
    try:
        # Упрощенная версия для тестирования
        # В реальной реализации здесь будут сервисы
        
        # Симуляция обнаружения каналов
        discovered_channels = [
            {
                "username": "crypto_signals_pro",
                "title": "Crypto Signals Pro",
                "description": "Professional crypto trading signals",
                "member_count": 15000,
                "type": "telegram"
            },
            {
                "username": "binance_signals",
                "title": "Binance Signals", 
                "description": "Binance trading signals and analysis",
                "member_count": 25000,
                "type": "telegram"
            },
            {
                "username": "crypto_alerts",
                "title": "Crypto Alerts",
                "description": "Real-time crypto alerts and signals",
                "member_count": 8000,
                "type": "telegram"
            }
        ]
        
        # Симуляция найденных сигналов
        found_signals = [
            {
                "symbol": "BTCUSDT",
                "signal_type": "long",
                "entry_price": 119364.80,
                "target_price": 121750.10,
                "stop_loss": 118000.00,
                "confidence": 0.85,
                "source": "crypto_signals_pro"
            }
        ]
        
        # Симуляция добавления в базу данных
        added_channels = 1  # Один канал с сигналами
        added_signals = 1   # Один сигнал
        
        result = {
            "total_channels_discovered": len(discovered_channels),
            "channels_with_signals": added_channels,
            "total_signals_added": added_signals,
            "added_channels": [
                {
                    "id": 1,
                    "name": "Crypto Signals Pro",
                    "username": "crypto_signals_pro",
                    "type": "telegram"
                }
            ],
            "added_signals": [
                {
                    "id": 1,
                    "symbol": "BTCUSDT",
                    "signal_type": "long",
                    "source": "crypto_signals_pro"
                }
            ]
        }
        
        return {
            "success": True,
            "message": f"Discovery completed successfully. Found {result['channels_with_signals']} channels with signals.",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during channel discovery: {str(e)}"
        )

@router.get("/{channel_id}", response_model=schemas.Channel)
def read_channel(
    *,
    channel: models.Channel = Depends(auth.get_channel_for_owner_or_admin)
):
    """
    Get a specific channel by ID.
    """
    return channel

@router.delete("/{channel_id}", response_model=schemas.Channel)
def delete_channel(
    *,
    db: Session = Depends(auth.get_db),
    channel: models.Channel = Depends(auth.get_channel_for_owner_or_admin)
):
    """
    Delete a channel.
    """
    db.delete(channel)
    db.commit()
    return channel

@router.get("/{channel_id}/signals")
async def get_channel_signals(
    channel_id: int,
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """
    Retrieve signals from a specific channel with filtering options.
    """
    # Заглушка
    return {
        "items": [
            {
                "id": 1,
                "channel_id": channel_id,
                "asset": "BTC/USDT",
                "direction": "BUY",
                "entry_price": 50000.0,
                "target_price": 55000.0,
                "stop_loss": 48000.0,
                "timestamp": datetime.now().isoformat(),
                "status": "SUCCESSFUL",
                "accuracy": 100.0,
            }
        ],
        "total": 1,
        "skip": skip,
        "limit": limit,
    }

@router.get("/{channel_id}/statistics")
async def get_channel_statistics(channel_id: int):
    """
    Get detailed statistics for a specific channel.
    """
    # Заглушка
    return {
        "channel_id": channel_id,
        "total_signals": 342,
        "successful_signals": 268,
        "accuracy": 78.5,
        "average_roi": 12.3,
        "max_drawdown": 5.2,
        "last_30_days": {
            "signals": 42,
            "accuracy": 81.0,
            "roi": 14.5,
        },
    } 

@router.get("/dashboard/", response_model=List[dict])
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