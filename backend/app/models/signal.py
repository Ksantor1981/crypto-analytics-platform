from sqlalchemy import Column, String, Float, Integer, Enum, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from .base import BaseModel

class SignalDirection(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"

class SignalStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESSFUL = "SUCCESSFUL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class Signal(BaseModel):
    """
    Model representing a trading signal from a channel
    """
    __tablename__ = "signals"
    
    # Relationships
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False, index=True)
    channel = relationship("Channel", back_populates="signals")
    
    # Signal details
    asset = Column(String(20), nullable=False, index=True)  # e.g., BTC/USDT
    direction = Column(Enum(SignalDirection), nullable=False)
    entry_price = Column(Float, nullable=False)
    target_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    
    # Original message
    original_text = Column(Text, nullable=True)
    message_timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Result
    status = Column(Enum(SignalStatus), default=SignalStatus.PENDING)
    exit_price = Column(Float, nullable=True)
    exit_timestamp = Column(DateTime, nullable=True)
    profit_loss = Column(Float, nullable=True)  # In percentage
    
    # ML prediction
    ml_success_probability = Column(Float, nullable=True)
    is_ml_prediction_correct = Column(Boolean, nullable=True)
    
    def __repr__(self):
        return f"<Signal {self.asset} {self.direction} at {self.entry_price}>" 