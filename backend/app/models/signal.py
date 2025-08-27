from sqlalchemy import Column, String, Float, Integer, Enum, DateTime, ForeignKey, Text, Boolean, Numeric, JSON
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from decimal import Decimal

from .base import BaseModel

class SignalDirection(str, enum.Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    BUY = "BUY"  # Keep for backward compatibility
    SELL = "SELL"  # Keep for backward compatibility

class SignalStatus(str, enum.Enum):
    PENDING = "PENDING"
    ENTRY_HIT = "ENTRY_HIT"
    TP1_HIT = "TP1_HIT"
    TP2_HIT = "TP2_HIT"
    TP3_HIT = "TP3_HIT"
    SL_HIT = "SL_HIT"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"

class Signal(BaseModel):
    """
    Model representing a trading signal from a channel
    """
    __tablename__ = "signals"
    
    # Relationships
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False, index=True)
    channel = relationship("Channel", back_populates="signals")
    result = relationship("SignalResult", back_populates="signal", uselist=False, cascade="all, delete-orphan")
    positions = relationship("TradingPosition", back_populates="signal", cascade="all, delete-orphan")
    
    # Signal details
    asset = Column(String(20), nullable=False, index=True)  # e.g., BTC/USDT
    symbol = Column(String(20), nullable=False, index=True)  # Alternative name for asset (for compatibility)
    direction = Column(Enum(SignalDirection), nullable=False)
    entry_price = Column(Numeric(20, 8), nullable=False)  # More precise than Float
    
    # Multiple targets support
    tp1_price = Column(Numeric(20, 8), nullable=True)  # Target 1
    tp2_price = Column(Numeric(20, 8), nullable=True)  # Target 2
    tp3_price = Column(Numeric(20, 8), nullable=True)  # Target 3
    stop_loss = Column(Numeric(20, 8), nullable=True)
    
    # Entry zone support (for range entries)
    entry_price_low = Column(Numeric(20, 8), nullable=True)
    entry_price_high = Column(Numeric(20, 8), nullable=True)
    
    # Original message
    original_text = Column(Text, nullable=True)
    message_timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)  # Alternative name for compatibility
    telegram_message_id = Column(String(50), nullable=True)  # For tracking
    
    # Signal execution tracking
    status = Column(Enum(SignalStatus), default=SignalStatus.PENDING)
    entry_hit_at = Column(DateTime(timezone=True), nullable=True)
    tp1_hit_at = Column(DateTime(timezone=True), nullable=True)
    tp2_hit_at = Column(DateTime(timezone=True), nullable=True)
    tp3_hit_at = Column(DateTime(timezone=True), nullable=True)
    sl_hit_at = Column(DateTime(timezone=True), nullable=True)
    
    # Result tracking
    final_exit_price = Column(Numeric(20, 8), nullable=True)
    final_exit_timestamp = Column(DateTime(timezone=True), nullable=True)
    profit_loss_percentage = Column(Numeric(10, 4), nullable=True)  # ROI in percentage
    profit_loss_absolute = Column(Numeric(20, 8), nullable=True)  # Absolute profit/loss
    
    # Signal lifecycle
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Auto-expire after X hours
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(String(255), nullable=True)
    
    # Analysis flags
    is_successful = Column(Boolean, nullable=True)  # Based on our success criteria
    reached_tp1 = Column(Boolean, default=False, nullable=False)
    reached_tp2 = Column(Boolean, default=False, nullable=False)
    reached_tp3 = Column(Boolean, default=False, nullable=False)
    hit_stop_loss = Column(Boolean, default=False, nullable=False)
    
    # ML prediction
    ml_success_probability = Column(Numeric(5, 4), nullable=True)  # 0.0 to 1.0
    ml_predicted_roi = Column(Numeric(10, 4), nullable=True)
    is_ml_prediction_correct = Column(Boolean, nullable=True)
    ml_prediction = Column(JSON, nullable=True)  # Full ML prediction data
    
    # Signal quality indicators
    confidence_score = Column(Numeric(5, 2), nullable=True)  # 0-100 quality score
    risk_reward_ratio = Column(Numeric(10, 4), nullable=True)
    
    @property
    def duration_hours(self) -> float:
        """Calculate signal duration in hours"""
        if not self.final_exit_timestamp:
            return None
        duration = self.final_exit_timestamp - self.created_at
        return duration.total_seconds() / 3600
    
    @property
    def is_expired(self) -> bool:
        """Check if signal has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def best_target_hit(self) -> str:
        """Get the highest target that was hit"""
        if self.reached_tp3:
            return "TP3"
        elif self.reached_tp2:
            return "TP2" 
        elif self.reached_tp1:
            return "TP1"
        elif self.hit_stop_loss:
            return "SL"
        else:
            return "NONE"
    
    def calculate_roi(self, exit_price: Decimal = None) -> Decimal:
        """Calculate ROI for the signal"""
        if not exit_price:
            exit_price = self.final_exit_price
        
        if not exit_price or not self.entry_price:
            return Decimal('0')
        
        if self.direction in [SignalDirection.LONG, SignalDirection.BUY]:
            roi = ((exit_price - self.entry_price) / self.entry_price) * 100
        else:  # SHORT/SELL
            roi = ((self.entry_price - exit_price) / self.entry_price) * 100
        
        return round(roi, 4)
    
    def __repr__(self):
        return f"<Signal {self.asset} {self.direction} at {self.entry_price} - {self.status}>"


class TelegramSignal(BaseModel):
    """
    Simplified model for Telegram signals - for direct integration
    """
    __tablename__ = "telegram_signals"
    
    # Basic signal info
    symbol = Column(String(20), nullable=False, index=True)  # e.g., BTCUSDT
    signal_type = Column(String(10), nullable=False)  # long/short
    entry_price = Column(Numeric(20, 8), nullable=True)
    target_price = Column(Numeric(20, 8), nullable=True)
    stop_loss = Column(Numeric(20, 8), nullable=True)
    
    # Signal metadata
    confidence = Column(Numeric(5, 4), default=0.5)  # 0.0 to 1.0
    source = Column(String(100), nullable=False)  # Source channel/bot
    original_text = Column(Text, nullable=True)
    signal_metadata = Column(JSON, nullable=True)  # Additional data (renamed from metadata)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)  # Add timestamp field
    
    # Status tracking
    status = Column(String(20), default="PENDING", index=True)
    
    def __repr__(self):
        return f"<TelegramSignal {self.symbol} {self.signal_type} - {self.status}>" 