from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from .signal import ChannelSignalStats


class ChannelBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Название канала")
    url: str = Field(..., max_length=255, description="URL канала")
    description: Optional[str] = Field(None, description="Описание канала")
    category: Optional[str] = Field(None, max_length=100, description="Категория")
    platform: str = Field("telegram", max_length=50, description="Платформа")


class ChannelCreate(ChannelBase):
    pass


class ChannelUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class ChannelInDB(ChannelBase):
    id: int
    owner_id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class ChannelResponse(ChannelBase):
    id: int
    owner_id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class ChannelWithStats(ChannelResponse):
    stats: Optional[ChannelSignalStats] = None


class ChannelListResponse(BaseModel):
    channels: List[ChannelResponse]
    total: int
    page: int
    size: int
    pages: int