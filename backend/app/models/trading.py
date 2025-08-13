"""
Trading models for auto-trading system
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum, JSON, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from .base import BaseModel

class ExchangeType(str, enum.Enum):
    BYBIT = "bybit"
    BINANCE = "binance"
    COINBASE = "coinbase"

class OrderType(str, enum.Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_MARKET = "stop_market"
    STOP_LIMIT = "stop_limit"

class OrderSide(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"

class PositionSide(str, enum.Enum):
    LONG = "long"
    SHORT = "short"

class StrategyType(str, enum.Enum):
    SIGNAL_FOLLOWING = "signal_following"
    GRID_TRADING = "grid_trading"
    DCA = "dca"
    SCALPING = "scalping"

class TradingAccount(BaseModel):
    """
    Model representing user's trading account
    """
    __tablename__ = "trading_accounts"
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="trading_accounts")
    
    # Account details
    name = Column(String(255), nullable=False)
    exchange = Column(Enum(ExchangeType), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # API credentials (encrypted)
    api_key_encrypted = Column(Text, nullable=False)
    api_secret_encrypted = Column(Text, nullable=False)
    passphrase_encrypted = Column(Text, nullable=True)  # For some exchanges
    
    # Account settings
    max_position_size = Column(Numeric(10, 2), default=100.0)  # Max position size in USD
    max_daily_loss = Column(Numeric(10, 2), default=50.0)  # Max daily loss in USD
    risk_per_trade = Column(Float, default=0.02)  # 2% risk per trade
    auto_trading_enabled = Column(Boolean, default=False)
    
    # Trading limits
    max_open_positions = Column(Integer, default=5)
    min_signal_confidence = Column(Float, default=0.7)
    
    # Account balance tracking
    total_balance = Column(Numeric(15, 8), default=0.0)
    available_balance = Column(Numeric(15, 8), default=0.0)
    total_pnl = Column(Numeric(15, 8), default=0.0)
    
    # Timestamps
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    positions = relationship("TradingPosition", back_populates="account")
    orders = relationship("TradingOrder", back_populates="account")
    strategies = relationship("TradingStrategy", back_populates="account")

class TradingPosition(BaseModel):
    """
    Model representing open trading positions
    """
    __tablename__ = "trading_positions"
    
    # Account relationship
    account_id = Column(Integer, ForeignKey("trading_accounts.id"), nullable=False, index=True)
    account = relationship("TradingAccount", back_populates="positions")
    
    # Signal relationship (optional)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=True, index=True)
    signal = relationship("Signal", back_populates="positions")
    
    # Position details
    symbol = Column(String(20), nullable=False, index=True)  # e.g., BTCUSDT
    side = Column(Enum(PositionSide), nullable=False)
    size = Column(Numeric(15, 8), nullable=False)  # Position size
    entry_price = Column(Numeric(20, 8), nullable=False)
    
    # Risk management
    stop_loss = Column(Numeric(20, 8), nullable=True)
    take_profit = Column(Numeric(20, 8), nullable=True)
    trailing_stop = Column(Boolean, default=False)
    trailing_stop_distance = Column(Float, nullable=True)  # Percentage
    
    # Current state
    current_price = Column(Numeric(20, 8), nullable=True)
    unrealized_pnl = Column(Numeric(15, 8), default=0.0)
    unrealized_pnl_percent = Column(Float, default=0.0)
    
    # Position status
    is_open = Column(Boolean, default=True)
    opened_at = Column(DateTime(timezone=True), default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Exit details
    exit_price = Column(Numeric(20, 8), nullable=True)
    realized_pnl = Column(Numeric(15, 8), default=0.0)
    realized_pnl_percent = Column(Float, default=0.0)
    
    # Exchange details
    exchange_order_id = Column(String(255), nullable=True)
    exchange_position_id = Column(String(255), nullable=True)
    
    # Metadata
    position_metadata = Column(JSON, nullable=True)  # Additional exchange-specific data

class TradingOrder(BaseModel):
    """
    Model representing trading orders
    """
    __tablename__ = "trading_orders"
    
    # Account relationship
    account_id = Column(Integer, ForeignKey("trading_accounts.id"), nullable=False, index=True)
    account = relationship("TradingAccount", back_populates="orders")
    
    # Position relationship (optional)
    position_id = Column(Integer, ForeignKey("trading_positions.id"), nullable=True, index=True)
    position = relationship("TradingPosition")
    
    # Order details
    symbol = Column(String(20), nullable=False, index=True)
    order_type = Column(Enum(OrderType), nullable=False)
    side = Column(Enum(OrderSide), nullable=False)
    quantity = Column(Numeric(15, 8), nullable=False)
    price = Column(Numeric(20, 8), nullable=True)  # For limit orders
    
    # Order status
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    filled_quantity = Column(Numeric(15, 8), default=0.0)
    average_fill_price = Column(Numeric(20, 8), nullable=True)
    
    # Exchange details
    exchange_order_id = Column(String(255), nullable=True, unique=True)
    exchange_client_order_id = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    filled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    order_metadata = Column(JSON, nullable=True)  # Additional exchange-specific data

class TradingStrategy(BaseModel):
    """
    Model representing trading strategies
    """
    __tablename__ = "trading_strategies"
    
    # Account relationship
    account_id = Column(Integer, ForeignKey("trading_accounts.id"), nullable=False, index=True)
    account = relationship("TradingAccount", back_populates="strategies")
    
    # Strategy details
    name = Column(String(255), nullable=False)
    strategy_type = Column(Enum(StrategyType), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Strategy parameters
    parameters = Column(JSON, nullable=True)  # Strategy-specific parameters
    
    # Performance tracking
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    total_pnl = Column(Numeric(15, 8), default=0.0)
    win_rate = Column(Float, default=0.0)
    
    # Risk management
    max_drawdown = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now())
    last_executed_at = Column(DateTime(timezone=True), nullable=True)

class RiskManagement(BaseModel):
    """
    Модель для управления рисками пользователя
    """
    __tablename__ = "risk_management"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="risk_management")
    
    # Параметры управления рисками
    max_position_size_usd = Column(Numeric(10, 2), default=100.0)  # Максимальный размер позиции в USD
    max_daily_loss_usd = Column(Numeric(10, 2), default=50.0)  # Максимальный дневной убыток в USD
    max_portfolio_risk = Column(Float, default=0.05)  # Максимальный риск портфеля (5%)
    max_correlation = Column(Float, default=0.7)  # Максимальная корреляция между активами
    default_stop_loss_percent = Column(Float, default=0.02)  # Стандартный стоп-лосс (2%)
    trailing_stop_enabled = Column(Boolean, default=True)  # Включен ли трейлинг-стоп
    trailing_stop_distance = Column(Float, default=0.01)  # Дистанция трейлинг-стопа (1%)
    risk_per_trade = Column(Float, default=0.02)  # Риск на сделку (2%)
    max_positions_per_symbol = Column(Integer, default=1)  # Макс. позиций на символ
    max_total_positions = Column(Integer, default=5)  # Макс. общее количество позиций
    trading_hours_start = Column(String(5), default="00:00")  # Начало торговой сессии
    trading_hours_end = Column(String(5), default="23:59")  # Окончание торговой сессии
    weekend_trading = Column(Boolean, default=False)  # Торговля по выходным
    min_volume_usd = Column(Numeric(15, 2), default=1000000.0)  # Минимальный объем торгов
    max_spread_percent = Column(Float, default=0.005)  # Максимальный спред (0.5%)
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<RiskManagement(user_id={self.user_id})>"