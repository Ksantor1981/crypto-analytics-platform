"""
Telegram Integration API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

from ...core.database import get_db
from ...services.telegram_service import (
    BackendTelegramService, 
    collect_telegram_signals,
    get_channel_signals
)
from ...models.channel import Channel
from ...models.signal import Signal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/telegram", tags=["telegram"])

@router.post("/collect-signals")
async def trigger_signal_collection(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger signal collection from Telegram channels
    """
    try:
        # Run collection in background
        background_tasks.add_task(collect_telegram_signals, db)
        
        return {
            "success": True,
            "message": "Signal collection started in background",
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error triggering signal collection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start collection: {str(e)}")

@router.get("/collect-signals-sync")
async def collect_signals_sync(db: Session = Depends(get_db)):
    """
    Synchronously collect signals from Telegram channels
    """
    try:
        result = await collect_telegram_signals(db)
        
        return {
            "success": True,
            "data": result,
            "message": "Signal collection completed"
        }
        
    except Exception as e:
        logger.error(f"Error in synchronous signal collection: {e}")
        raise HTTPException(status_code=500, detail=f"Signal collection failed: {str(e)}")

@router.get("/channels")
async def get_telegram_channels(db: Session = Depends(get_db)):
    """
    Get list of configured Telegram channels
    """
    try:
        channels = db.query(Channel).filter(Channel.platform == 'telegram').all()
        
        channel_list = []
        for channel in channels:
            channel_data = {
                "id": channel.id,
                "name": channel.name,
                "url": channel.url,
                "description": channel.description,
                "category": channel.category,
                "is_active": channel.is_active,
                "signals_count": channel.signals_count,  # Исправлено с subscribers_count
                "accuracy": channel.accuracy,             # Используем правильное поле
                "created_at": channel.created_at.isoformat() if channel.created_at else None,
                "updated_at": channel.updated_at.isoformat() if channel.updated_at else None
            }
            channel_list.append(channel_data)
        
        return {
            "success": True,
            "data": channel_list,
            "total_channels": len(channel_list),
            "message": "Telegram channels retrieved"
        }
        
    except Exception as e:
        logger.error(f"Error getting Telegram channels: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get channels: {str(e)}")

@router.get("/channels/{channel_id}/signals")
async def get_channel_signals_endpoint(
    channel_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get signals from a specific Telegram channel
    """
    try:
        # Verify channel exists and is a Telegram channel
        channel = db.query(Channel).filter(
            Channel.id == channel_id,
            Channel.platform == 'telegram'
        ).first()
        
        if not channel:
            raise HTTPException(status_code=404, detail="Telegram channel not found")
        
        signals = await get_channel_signals(db, channel_id, limit)
        
        return {
            "success": True,
            "data": {
                "channel": {
                    "id": channel.id,
                    "name": channel.name,
                    "url": channel.url
                },
                "signals": signals,
                "total_signals": len(signals)
            },
            "message": f"Signals retrieved for channel {channel.name}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting channel signals: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get signals: {str(e)}")

@router.get("/channels/{channel_id}/statistics")
async def get_channel_statistics(
    channel_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed statistics for a Telegram channel
    """
    try:
        service = BackendTelegramService(db)
        stats = service.get_channel_statistics(channel_id)
        
        if "error" in stats:
            raise HTTPException(status_code=404, detail=stats["error"])
        
        return {
            "success": True,
            "data": stats,
            "message": "Channel statistics retrieved"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting channel statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@router.get("/signals/recent")
async def get_recent_telegram_signals(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get recent signals from all Telegram channels
    """
    try:
        signals = await get_channel_signals(db, None, limit)
        
        return {
            "success": True,
            "data": signals,
            "total_signals": len(signals),
            "message": "Recent Telegram signals retrieved"
        }
        
    except Exception as e:
        logger.error(f"Error getting recent signals: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get signals: {str(e)}")

@router.post("/channels/{channel_id}/toggle")
async def toggle_channel_status(
    channel_id: int,
    db: Session = Depends(get_db)
):
    """
    Toggle active status of a Telegram channel
    """
    try:
        channel = db.query(Channel).filter(
            Channel.id == channel_id,
            Channel.platform == 'telegram'
        ).first()
        
        if not channel:
            raise HTTPException(status_code=404, detail="Telegram channel not found")
        
        channel.is_active = not channel.is_active
        db.commit()
        
        status = "activated" if channel.is_active else "deactivated"
        
        return {
            "success": True,
            "data": {
                "channel_id": channel.id,
                "channel_name": channel.name,
                "is_active": channel.is_active
            },
            "message": f"Channel {channel.name} {status}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling channel status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to toggle status: {str(e)}")

@router.get("/health")
async def telegram_integration_health(db: Session = Depends(get_db)):
    """
    Health check for Telegram integration
    """
    try:
        service = BackendTelegramService(db)
        
        # Count channels and signals
        total_channels = db.query(Channel).filter(Channel.platform == 'telegram').count()
        active_channels = db.query(Channel).filter(
            Channel.platform == 'telegram',
            Channel.is_active == True
        ).count()
        total_signals = db.query(Signal).join(Channel).filter(
            Channel.platform == 'telegram'
        ).count()
        
        # Check if Telegram client can be initialized
        can_initialize = False
        error_message = None
        
        try:
            can_initialize = await service.initialize_telegram_client()
        except Exception as e:
            error_message = str(e)
        
        return {
            "success": True,
            "status": "healthy" if can_initialize else "degraded",
            "data": {
                "telegram_available": service.collector is not None,
                "can_initialize_client": can_initialize,
                "total_channels": total_channels,
                "active_channels": active_channels,
                "total_signals": total_signals,
                "error_message": error_message
            },
            "message": "Telegram integration health check completed"
        }
        
    except Exception as e:
        logger.error(f"Telegram health check failed: {e}")
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e),
            "message": "Telegram integration health check failed"
        } 