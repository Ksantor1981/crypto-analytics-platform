"""
Channel model for storing Telegram channel information
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import BaseModel


class Channel(BaseModel):
    """Model for storing Telegram channel information"""
    
    __tablename__ = "channels"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    platform = Column(String(50), default="telegram", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    subscribers_count = Column(Integer, nullable=True)
    category = Column(String(100), nullable=True)
    priority = Column(Integer, default=1, nullable=False)
    expected_accuracy = Column(String(50), nullable=True)
    status = Column(String(50), default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="channels")
    signals = relationship("Signal", back_populates="channel", cascade="all, delete-orphan")
    performance_metrics = relationship("PerformanceMetric", back_populates="channel", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Channel(username='{self.username}', name='{self.name}', platform='{self.platform}')>" 