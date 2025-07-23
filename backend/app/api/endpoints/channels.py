from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from sqlalchemy.orm import Session

from app import models, schemas
from app.core import auth
from app.core.database import get_db
from app.models.user import UserRole
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