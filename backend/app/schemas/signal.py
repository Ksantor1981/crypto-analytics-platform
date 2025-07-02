from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Перечисления для направления сигнала и статуса
class SignalDirection(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class SignalStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESSFUL = "SUCCESSFUL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

# Базовая схема для общих полей
class SignalBase(BaseModel):
    asset: str = Field(..., description="Trading pair (e.g., BTC/USDT)", min_length=1, max_length=20)
    direction: SignalDirection
    entry_price: float = Field(..., description="Entry price", gt=0)
    target_price: Optional[float] = Field(None, description="Target price", gt=0)
    stop_loss: Optional[float] = Field(None, description="Stop loss price", gt=0)
    original_text: Optional[str] = Field(None, description="Original message text")

# Схема для создания нового сигнала
class SignalCreate(SignalBase):
    channel_id: int = Field(..., description="ID of the channel")
    message_timestamp: Optional[datetime] = Field(None, description="Timestamp of the original message")

# Схема для обновления сигнала
class SignalUpdate(BaseModel):
    status: Optional[SignalStatus] = Field(None, description="Status of the signal")
    exit_price: Optional[float] = Field(None, description="Exit price", gt=0)
    exit_timestamp: Optional[datetime] = Field(None, description="Timestamp of exit")
    profit_loss: Optional[float] = Field(None, description="Profit/loss in percentage")
    ml_success_probability: Optional[float] = Field(None, description="ML prediction of success probability", ge=0, le=1)
    is_ml_prediction_correct: Optional[bool] = Field(None, description="Whether ML prediction was correct")

# Схема для ответа с сигналом
class Signal(SignalBase):
    id: int
    channel_id: int
    status: SignalStatus
    message_timestamp: datetime
    exit_price: Optional[float] = None
    exit_timestamp: Optional[datetime] = None
    profit_loss: Optional[float] = None
    ml_success_probability: Optional[float] = None
    is_ml_prediction_correct: Optional[bool] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Схема для списка сигналов с пагинацией
class SignalList(BaseModel):
    items: List[Signal]
    total: int
    skip: int
    limit: int 