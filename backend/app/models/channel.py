from sqlalchemy import Column, String, Float, Integer, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from .base import BaseModel

class Channel(BaseModel):
    """
    Model representing a crypto signal channel (Telegram, Discord, etc.)
    """
    __tablename__ = "channels"
    
    name = Column(String(255), nullable=False, index=True)
    platform = Column(String(50), nullable=False, index=True)  # telegram, discord, etc.
    url = Column(String(255), nullable=False, unique=True)
    category = Column(String(50), nullable=True, index=True)
    description = Column(Text, nullable=True)
    
    # Channel statistics
    accuracy = Column(Float, nullable=True)
    signals_count = Column(Integer, default=0)
    successful_signals = Column(Integer, default=0)
    average_roi = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Ownership
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="channels")
    
    # Relationships
    signals = relationship("Signal", back_populates="channel", cascade="all, delete-orphan")
    performance_metrics = relationship("PerformanceMetric", back_populates="channel", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Channel {self.name} ({self.platform})>" 