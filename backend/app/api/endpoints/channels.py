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

    channel_data = channel_in.dict()
    if not channel_data.get('username'):
        import re
        url = channel_data.get('url', '')
        name = channel_data.get('name', '')
        username = re.sub(r'[^a-zA-Z0-9_]', '_', url.split('/')[-1] or name)[:100] or f"channel_{current_user.id}"
        channel_data['username'] = username

    db_channel = models.Channel(**channel_data, owner_id=current_user.id)
    db.add(db_channel)
    db.commit()
    db.refresh(db_channel)
    return db_channel

@router.get("/", response_model=List[schemas.Channel])
def read_channels(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    sort: Optional[str] = Query("accuracy_desc", description="Sort: accuracy_desc (default), accuracy_asc (anti-rating)"),
    current_user: Optional[models.User] = Depends(auth.get_optional_current_user)
):
    """
    Retrieve channels. If authenticated, shows user's channels first.
    sort=accuracy_asc — для антирейтинга (худшие первыми).
    """
    # Redis cache (only when unauthenticated)
    if current_user is None:
        try:
            from app.core.redis_cache import cache_get, cache_set, key_channels_list, CACHE_TTL_CHANNELS
            cache_key = key_channels_list(sort or "accuracy_desc", skip, limit)
            cached = cache_get(cache_key)
            if cached is not None:
                return [schemas.Channel(**c) for c in cached]
        except Exception:
            pass

    query = db.query(models.Channel).filter(models.Channel.is_active == True)
    order_accuracy = models.Channel.accuracy.desc()
    if sort == "accuracy_asc":
        order_accuracy = models.Channel.accuracy.asc()
    if current_user:
        query = query.order_by(
            (models.Channel.owner_id == current_user.id).desc(),
            order_accuracy
        )
    else:
        query = query.order_by(order_accuracy)
    channels = query.offset(skip).limit(limit).all()

    # Cache for unauthenticated
    if current_user is None:
        try:
            from app.core.redis_cache import cache_set, key_channels_list, CACHE_TTL_CHANNELS
            cache_set(key_channels_list(sort or "accuracy_desc", skip, limit),
                      [schemas.Channel.model_validate(ch).model_dump(mode="json") for ch in channels],
                      CACHE_TTL_CHANNELS)
        except Exception:
            pass
    return channels

@router.post("/discover", response_model=dict)
def discover_channels(
    *,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """
    DEV/CI-only: симулирует обнаружение каналов с фиктивными цифрами.

    В production (`ENVIRONMENT == "production"` или `DEBUG = false`) endpoint
    возвращает 404, чтобы фиктивные каналы (Crypto Signals Pro 85%, Binance
    Signals 25k subscribers и т.п.) не утекали в реальные данные продукта.
    Реальный discovery делается через scheduler / collection_pipeline.
    """
    from app.core.config import get_settings as _get_settings
    _s = _get_settings()
    _env = (getattr(_s, "ENVIRONMENT", "development") or "development").lower()
    _debug = bool(getattr(_s, "DEBUG", True))
    if _env == "production" or not _debug:
        raise HTTPException(status_code=404, detail="Mock discovery disabled in production")
    try:
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

@router.get("/dashboard/", response_model=List[dict])
def get_channels_dashboard(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """Get channel dashboard data (authenticated-only). Must be before /{channel_id}."""
    query = db.query(Channel)
    total = query.count()
    channels = query.order_by(Channel.created_at.desc()).offset(skip).limit(limit).all()
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


@router.get("/{channel_id}", response_model=schemas.Channel)
def read_channel(
    channel_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a specific channel by ID (public).
    """
    channel = db.query(models.Channel).filter(models.Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel

@router.delete("/{channel_id}", response_model=schemas.Channel)
def delete_channel(
    *,
    db: Session = Depends(get_db),
    channel: models.Channel = Depends(auth.get_channel_for_owner_or_admin)
):
    """
    Delete a channel.
    """
    db.delete(channel)
    db.commit()
    return channel

@router.get("/{channel_id}/signals")
def get_channel_signals(
    channel_id: int,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """
    Retrieve signals from a specific channel (authenticated-only).
    Сигналы — премиум-функционал; Free может видеть только антирейтинг
    каналов (`GET /api/v1/channels/`) и их базовую статистику.
    """
    from app.services.signal_service import SignalService
    from app.schemas.signal import SignalFilterParams

    channel = db.query(models.Channel).filter(models.Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    signal_service = SignalService(db)
    filters = SignalFilterParams(channel_id=channel_id)
    signals, total = signal_service.get_signals(skip=skip, limit=limit, filters=filters)

    items = []
    for s in signals:
        items.append({
            "id": s.id,
            "channel_id": s.channel_id,
            "asset": s.asset,
            "symbol": s.asset,
            "direction": s.direction.value if hasattr(s.direction, "value") else str(s.direction),
            "entry_price": float(s.entry_price) if s.entry_price else None,
            "tp1_price": float(s.tp1_price) if s.tp1_price else None,
            "stop_loss": float(s.stop_loss) if s.stop_loss else None,
            "status": s.status.value if hasattr(s.status, "value") else str(s.status),
            "profit_loss_percentage": float(s.profit_loss_percentage) if s.profit_loss_percentage else None,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/{channel_id}/statistics")
def get_channel_statistics(
    channel_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """
    Get detailed statistics for a specific channel (authenticated-only).
    """
    from app.services.signal_service import SignalService
    from app.schemas.signal import SignalFilterParams

    channel = db.query(models.Channel).filter(models.Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    signal_service = SignalService(db)
    filters = SignalFilterParams(channel_id=channel_id)
    stats = signal_service.get_signal_stats(filters)
    total = stats.total_signals
    successful = stats.successful_signals
    accuracy = (successful / total * 100) if total > 0 else 0
    return {
        "channel_id": channel_id,
        "total_signals": total,
        "successful_signals": successful,
        "accuracy": round(accuracy, 1),
        "average_roi": round(stats.average_roi, 2),
        "max_drawdown": 0,
    } 