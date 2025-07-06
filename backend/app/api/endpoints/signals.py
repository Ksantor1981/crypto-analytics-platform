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
    SignalStatus
)
from app.models.user import User
from app.core.rate_limiter import limiter
from app.core.logging import get_logger
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

# Pydantic модели для сигналов
class TelegramSignalCreate(BaseModel):
    """Модель для создания сигнала из Telegram"""
    symbol: str = Field(..., description="Торговая пара (например, BTCUSDT)")
    signal_type: str = Field(..., description="Тип сигнала: long/short")
    entry_price: Optional[float] = Field(None, description="Цена входа")
    target_price: Optional[float] = Field(None, description="Целевая цена")
    stop_loss: Optional[float] = Field(None, description="Стоп-лосс")
    confidence: float = Field(0.5, ge=0.0, le=1.0, description="Уверенность в сигнале")
    source: str = Field(..., description="Источник сигнала")
    original_text: Optional[str] = Field(None, description="Оригинальный текст сообщения")
    metadata: Optional[Dict] = Field(None, description="Дополнительные метаданные")

class TelegramSignalResponse(BaseModel):
    """Модель ответа для сигнала"""
    id: int
    symbol: str
    signal_type: str
    entry_price: Optional[float]
    target_price: Optional[float]
    stop_loss: Optional[float]
    confidence: float
    source: str
    status: str
    created_at: datetime
    metadata: Optional[Dict]

# Временное хранилище сигналов (в продакшене использовать БД)
signals_storage = []
signal_id_counter = 1

@router.post("/signals/", response_model=TelegramSignalResponse)
@limiter.limit("100/hour")
async def create_signal(
    request: Request,
    signal: TelegramSignalCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Создание нового торгового сигнала из Telegram
    """
    global signal_id_counter
    
    try:
        # Валидация данных
        if not signal.symbol or len(signal.symbol) < 3:
            raise HTTPException(status_code=400, detail="Некорректный символ")
        
        if signal.signal_type.lower() not in ['long', 'short']:
            raise HTTPException(status_code=400, detail="Тип сигнала должен быть 'long' или 'short'")
        
        # Создаем сигнал
        new_signal = {
            "id": signal_id_counter,
            "symbol": signal.symbol.upper(),
            "signal_type": signal.signal_type.lower(),
            "entry_price": signal.entry_price,
            "target_price": signal.target_price,
            "stop_loss": signal.stop_loss,
            "confidence": signal.confidence,
            "source": signal.source,
            "original_text": signal.original_text,
            "metadata": signal.metadata or {},
            "status": "active",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Сохраняем в хранилище
        signals_storage.append(new_signal)
        signal_id_counter += 1
        
        # Логируем создание сигнала
        logger.info(
            "signal_created",
            extra={
                "signal_id": new_signal["id"],
                "symbol": new_signal["symbol"],
                "signal_type": new_signal["signal_type"],
                "source": new_signal["source"],
                "confidence": new_signal["confidence"]
            }
        )
        
        # Добавляем фоновую задачу для обработки сигнала
        background_tasks.add_task(process_signal_background, new_signal)
        
        return TelegramSignalResponse(**new_signal)
        
    except Exception as e:
        logger.error(f"Ошибка создания сигнала: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания сигнала")

@router.get("/signals/", response_model=List[TelegramSignalResponse])
@limiter.limit("200/hour")
async def get_signals(
    skip: int = 0,
    limit: int = 100,
    symbol: Optional[str] = None,
    signal_type: Optional[str] = None,
    source: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Получение списка сигналов с фильтрацией
    """
    try:
        # Фильтрация сигналов
        filtered_signals = signals_storage.copy()
        
        if symbol:
            filtered_signals = [s for s in filtered_signals if s["symbol"] == symbol.upper()]
        
        if signal_type:
            filtered_signals = [s for s in filtered_signals if s["signal_type"] == signal_type.lower()]
        
        if source:
            filtered_signals = [s for s in filtered_signals if source.lower() in s["source"].lower()]
        
        if status:
            filtered_signals = [s for s in filtered_signals if s["status"] == status.lower()]
        
        # Пагинация
        paginated_signals = filtered_signals[skip:skip + limit]
        
        # Сортировка по дате создания (новые первыми)
        paginated_signals.sort(key=lambda x: x["created_at"], reverse=True)
        
        return [TelegramSignalResponse(**signal) for signal in paginated_signals]
        
    except Exception as e:
        logger.error(f"Ошибка получения сигналов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения сигналов")

@router.get("/signals/{signal_id}", response_model=TelegramSignalResponse)
@limiter.limit("300/hour")
async def get_signal(
    signal_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Получение конкретного сигнала по ID
    """
    try:
        signal = next((s for s in signals_storage if s["id"] == signal_id), None)
        
        if not signal:
            raise HTTPException(status_code=404, detail="Сигнал не найден")
        
        return TelegramSignalResponse(**signal)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения сигнала {signal_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения сигнала")

@router.put("/signals/{signal_id}/status")
@limiter.limit("100/hour")
async def update_signal_status(
    signal_id: int,
    status: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Обновление статуса сигнала
    """
    try:
        if status not in ['active', 'completed', 'failed', 'cancelled']:
            raise HTTPException(status_code=400, detail="Недопустимый статус")
        
        signal = next((s for s in signals_storage if s["id"] == signal_id), None)
        
        if not signal:
            raise HTTPException(status_code=404, detail="Сигнал не найден")
        
        old_status = signal["status"]
        signal["status"] = status
        signal["updated_at"] = datetime.now(timezone.utc)
        
        logger.info(
            "signal_status_updated",
            extra={
                "signal_id": signal_id,
                "old_status": old_status,
                "new_status": status
            }
        )
        
        return {"message": "Статус обновлен", "signal_id": signal_id, "status": status}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка обновления статуса сигнала {signal_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления статуса")

@router.get("/signals/stats", response_model=SignalStats)
@limiter.limit("50/hour")
async def get_signals_stats(
    db: AsyncSession = Depends(get_db)
):
    """
    Получение статистики по сигналам
    """
    try:
        if not signals_storage:
            return SignalStats(
                total_signals=0,
                active_signals=0,
                successful_signals=0,
                failed_signals=0,
                avg_confidence=0.0,
                sources={},
                symbols={}
            )
        
        total_signals = len(signals_storage)
        active_signals = len([s for s in signals_storage if s["status"] == "active"])
        successful_signals = len([s for s in signals_storage if s["status"] == "completed"])
        failed_signals = len([s for s in signals_storage if s["status"] == "failed"])
        
        avg_confidence = sum(s["confidence"] for s in signals_storage) / total_signals
        
        # Статистика по источникам
        sources = {}
        for signal in signals_storage:
            source = signal["source"]
            sources[source] = sources.get(source, 0) + 1
        
        # Статистика по символам
        symbols = {}
        for signal in signals_storage:
            symbol = signal["symbol"]
            symbols[symbol] = symbols.get(symbol, 0) + 1
        
        return SignalStats(
            total_signals=total_signals,
            active_signals=active_signals,
            successful_signals=successful_signals,
            failed_signals=failed_signals,
            avg_confidence=round(avg_confidence, 3),
            sources=sources,
            symbols=symbols
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статистики")

@router.delete("/signals/{signal_id}")
@limiter.limit("50/hour")
async def delete_signal(
    signal_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Удаление сигнала
    """
    try:
        signal_index = next((i for i, s in enumerate(signals_storage) if s["id"] == signal_id), None)
        
        if signal_index is None:
            raise HTTPException(status_code=404, detail="Сигнал не найден")
        
        deleted_signal = signals_storage.pop(signal_index)
        
        logger.info(
            "signal_deleted",
            extra={
                "signal_id": signal_id,
                "symbol": deleted_signal["symbol"],
                "source": deleted_signal["source"]
            }
        )
        
        return {"message": "Сигнал удален", "signal_id": signal_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка удаления сигнала {signal_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления сигнала")

@router.post("/signals/batch", response_model=Dict)
@limiter.limit("10/hour")
async def create_signals_batch(
    signals: List[TelegramSignalCreate],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Создание пакета сигналов
    """
    global signal_id_counter
    
    try:
        if len(signals) > 50:
            raise HTTPException(status_code=400, detail="Максимум 50 сигналов за раз")
        
        created_signals = []
        errors = []
        
        for signal_data in signals:
            try:
                # Валидация
                if not signal_data.symbol or len(signal_data.symbol) < 3:
                    errors.append(f"Некорректный символ: {signal_data.symbol}")
                    continue
                
                if signal_data.signal_type.lower() not in ['long', 'short']:
                    errors.append(f"Некорректный тип сигнала: {signal_data.signal_type}")
                    continue
                
                # Создаем сигнал
                new_signal = {
                    "id": signal_id_counter,
                    "symbol": signal_data.symbol.upper(),
                    "signal_type": signal_data.signal_type.lower(),
                    "entry_price": signal_data.entry_price,
                    "target_price": signal_data.target_price,
                    "stop_loss": signal_data.stop_loss,
                    "confidence": signal_data.confidence,
                    "source": signal_data.source,
                    "original_text": signal_data.original_text,
                    "metadata": signal_data.metadata or {},
                    "status": "active",
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
                
                signals_storage.append(new_signal)
                created_signals.append(new_signal)
                signal_id_counter += 1
                
                # Фоновая обработка
                background_tasks.add_task(process_signal_background, new_signal)
                
            except Exception as e:
                errors.append(f"Ошибка создания сигнала: {str(e)}")
        
        logger.info(
            "batch_signals_created",
            extra={
                "total_requested": len(signals),
                "created": len(created_signals),
                "errors": len(errors)
            }
        )
        
        return {
            "created": len(created_signals),
            "errors": len(errors),
            "error_details": errors,
            "signal_ids": [s["id"] for s in created_signals]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка пакетного создания сигналов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка пакетного создания сигналов")

# Фоновая обработка сигналов
async def process_signal_background(signal: Dict):
    """
    Фоновая обработка сигнала
    """
    try:
        # Здесь можно добавить логику:
        # - Проверка цен в реальном времени
        # - Уведомления пользователей
        # - Интеграция с торговыми платформами
        # - Анализ эффективности
        
        logger.info(
            "signal_processed",
            extra={
                "signal_id": signal["id"],
                "symbol": signal["symbol"],
                "processing_time": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Ошибка фоновой обработки сигнала {signal['id']}: {e}")

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