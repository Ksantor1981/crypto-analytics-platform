from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from decimal import Decimal

# Перечисления для направления сигнала и статуса
class SignalDirection(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    BUY = "BUY"  # Keep for backward compatibility
    SELL = "SELL"  # Keep for backward compatibility

class SignalStatus(str, Enum):
    PENDING = "PENDING"
    ENTRY_HIT = "ENTRY_HIT"
    TP1_HIT = "TP1_HIT"
    TP2_HIT = "TP2_HIT"
    TP3_HIT = "TP3_HIT"
    SL_HIT = "SL_HIT"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"

# Базовая схема для общих полей
class SignalBase(BaseModel):
    asset: str = Field(..., description="Trading pair (e.g., BTC/USDT)", min_length=1, max_length=20)
    direction: SignalDirection
    entry_price: float = Field(..., description="Entry price", gt=0)
    
    # Multiple targets support
    tp1_price: Optional[float] = Field(None, description="Target 1 price", gt=0)
    tp2_price: Optional[float] = Field(None, description="Target 2 price", gt=0)
    tp3_price: Optional[float] = Field(None, description="Target 3 price", gt=0)
    stop_loss: Optional[float] = Field(None, description="Stop loss price", gt=0)
    
    # Entry zone support
    entry_price_low: Optional[float] = Field(None, description="Entry price low range", gt=0)
    entry_price_high: Optional[float] = Field(None, description="Entry price high range", gt=0)
    
    original_text: Optional[str] = Field(None, description="Original message text")

# Схема для создания нового сигнала
class SignalCreate(SignalBase):
    channel_id: int = Field(..., description="ID of the channel")
    message_timestamp: Optional[datetime] = Field(None, description="Timestamp of the original message")
    telegram_message_id: Optional[str] = Field(None, description="Telegram message ID")
    expires_at: Optional[datetime] = Field(None, description="Signal expiration time")

# Схема для обновления сигнала
class SignalUpdate(BaseModel):
    status: Optional[SignalStatus] = Field(None, description="Status of the signal")
    
    # Execution tracking
    entry_hit_at: Optional[datetime] = Field(None, description="When entry was hit")
    tp1_hit_at: Optional[datetime] = Field(None, description="When TP1 was hit")
    tp2_hit_at: Optional[datetime] = Field(None, description="When TP2 was hit")
    tp3_hit_at: Optional[datetime] = Field(None, description="When TP3 was hit")
    sl_hit_at: Optional[datetime] = Field(None, description="When SL was hit")
    
    # Result tracking
    final_exit_price: Optional[float] = Field(None, description="Final exit price", gt=0)
    final_exit_timestamp: Optional[datetime] = Field(None, description="Final exit timestamp")
    profit_loss_percentage: Optional[float] = Field(None, description="Profit/loss in percentage")
    profit_loss_absolute: Optional[float] = Field(None, description="Absolute profit/loss")
    
    # Analysis flags
    is_successful: Optional[bool] = Field(None, description="Whether signal was successful")
    reached_tp1: Optional[bool] = Field(None, description="Whether TP1 was reached")
    reached_tp2: Optional[bool] = Field(None, description="Whether TP2 was reached")
    reached_tp3: Optional[bool] = Field(None, description="Whether TP3 was reached")
    hit_stop_loss: Optional[bool] = Field(None, description="Whether stop loss was hit")
    
    # ML prediction
    ml_success_probability: Optional[float] = Field(None, description="ML prediction probability", ge=0, le=1)
    ml_predicted_roi: Optional[float] = Field(None, description="ML predicted ROI")
    is_ml_prediction_correct: Optional[bool] = Field(None, description="Whether ML prediction was correct")
    
    # Quality indicators
    confidence_score: Optional[float] = Field(None, description="Signal confidence score", ge=0, le=100)
    risk_reward_ratio: Optional[float] = Field(None, description="Risk/reward ratio")

# Схема для ответа с сигналом
class SignalResponse(SignalBase):
    id: int
    channel_id: int
    status: SignalStatus
    message_timestamp: datetime
    telegram_message_id: Optional[str] = None
    
    # Execution tracking
    entry_hit_at: Optional[datetime] = None
    tp1_hit_at: Optional[datetime] = None
    tp2_hit_at: Optional[datetime] = None
    tp3_hit_at: Optional[datetime] = None
    sl_hit_at: Optional[datetime] = None
    
    # Result tracking
    final_exit_price: Optional[float] = None
    final_exit_timestamp: Optional[datetime] = None
    profit_loss_percentage: Optional[float] = None
    profit_loss_absolute: Optional[float] = None
    
    # Analysis flags
    is_successful: Optional[bool] = None
    reached_tp1: bool = False
    reached_tp2: bool = False
    reached_tp3: bool = False
    hit_stop_loss: bool = False
    
    # ML prediction
    ml_success_probability: Optional[float] = None
    ml_predicted_roi: Optional[float] = None
    is_ml_prediction_correct: Optional[bool] = None
    
    # Quality indicators
    confidence_score: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    
    # Lifecycle
    expires_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Схема для списка сигналов с пагинацией
class SignalListResponse(BaseModel):
    signals: List[SignalResponse]
    total: int
    page: int
    size: int
    pages: int
    
# Схема для top performing signals
class TopSignal(BaseModel):
    id: int
    asset: str
    direction: SignalDirection
    entry_price: float
    final_exit_price: Optional[float] = None
    profit_loss_percentage: Optional[float] = None
    status: SignalStatus
    channel_name: Optional[str] = None
    message_timestamp: datetime
    best_target_hit: str = "NONE"

# Extended response with channel info
class SignalWithChannel(SignalResponse):
    channel_name: Optional[str] = None
    channel_username: Optional[str] = None

# Схема для фильтрации сигналов
class SignalFilterParams(BaseModel):
    channel_id: Optional[int] = None
    asset: Optional[str] = None
    direction: Optional[SignalDirection] = None
    status: Optional[SignalStatus] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    successful_only: Optional[bool] = None
    min_roi: Optional[float] = None
    max_roi: Optional[float] = None

# Схема для статистики сигналов
class SignalStats(BaseModel):
    total_signals: int = 0
    successful_signals: int = 0
    failed_signals: int = 0
    pending_signals: int = 0
    accuracy_percentage: float = 0.0
    average_roi: float = 0.0
    total_profit_loss: float = 0.0
    best_signal_roi: float = 0.0
    worst_signal_roi: float = 0.0
    average_duration_hours: float = 0.0
    
    # Target hit breakdown
    tp1_hits: int = 0
    tp2_hits: int = 0
    tp3_hits: int = 0
    sl_hits: int = 0
    expired_signals: int = 0

# Схема для статистики канала
class ChannelSignalStats(SignalStats):
    channel_id: int
    channel_name: Optional[str] = None
    period_days: int = 30

# Схема для статистики актива
class AssetPerformance(BaseModel):
    asset: str
    total_signals: int = 0
    successful_signals: int = 0
    accuracy_percentage: float = 0.0
    average_roi: float = 0.0
    total_profit_loss: float = 0.0
    risk_reward_ratio: float = 0.0 