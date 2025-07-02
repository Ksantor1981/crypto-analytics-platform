from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

# Базовая схема для общих полей
class ChannelBase(BaseModel):
    name: str = Field(..., description="Name of the channel", min_length=1, max_length=255)
    platform: str = Field(..., description="Platform (telegram, discord, etc.)", min_length=1, max_length=50)
    url: str = Field(..., description="URL of the channel", min_length=1, max_length=255)
    category: Optional[str] = Field(None, description="Category of signals (crypto, stocks, etc.)")
    description: Optional[str] = Field(None, description="Description of the channel")

# Схема для создания нового канала
class ChannelCreate(ChannelBase):
    pass

# Схема для обновления канала
class ChannelUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Name of the channel", min_length=1, max_length=255)
    platform: Optional[str] = Field(None, description="Platform (telegram, discord, etc.)", min_length=1, max_length=50)
    url: Optional[str] = Field(None, description="URL of the channel", min_length=1, max_length=255)
    category: Optional[str] = Field(None, description="Category of signals (crypto, stocks, etc.)")
    description: Optional[str] = Field(None, description="Description of the channel")
    is_active: Optional[bool] = Field(None, description="Whether the channel is active")
    is_verified: Optional[bool] = Field(None, description="Whether the channel is verified")

# Схема для ответа с каналом
class Channel(ChannelBase):
    id: int
    accuracy: Optional[float] = Field(None, description="Accuracy of signals (%)")
    signals_count: int = Field(0, description="Total number of signals")
    successful_signals: int = Field(0, description="Number of successful signals")
    average_roi: Optional[float] = Field(None, description="Average ROI (%)")
    max_drawdown: Optional[float] = Field(None, description="Maximum drawdown (%)")
    is_active: bool = Field(True, description="Whether the channel is active")
    is_verified: bool = Field(False, description="Whether the channel is verified")
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Схема для списка каналов с пагинацией
class ChannelList(BaseModel):
    items: List[Channel]
    total: int
    skip: int
    limit: int 