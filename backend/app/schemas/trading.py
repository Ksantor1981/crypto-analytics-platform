"""
Trading schemas for API
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum

from app.models.trading import (
    ExchangeType, OrderType, OrderSide, OrderStatus, 
    PositionSide, TradingStrategy
)

# Base schemas
class TradingAccountBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    exchange: ExchangeType
    max_position_size: Decimal = Field(default=100.0, ge=0)
    max_daily_loss: Decimal = Field(default=50.0, ge=0)
    risk_per_trade: float = Field(default=0.02, ge=0, le=1)
    auto_trading_enabled: bool = False
    max_open_positions: int = Field(default=5, ge=1, le=20)
    min_signal_confidence: float = Field(default=0.7, ge=0, le=1)

class TradingAccountCreate(TradingAccountBase):
    api_key: str = Field(..., min_length=1)
    api_secret: str = Field(..., min_length=1)
    passphrase: Optional[str] = None

class TradingAccountUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    max_position_size: Optional[Decimal] = Field(None, ge=0)
    max_daily_loss: Optional[Decimal] = Field(None, ge=0)
    risk_per_trade: Optional[float] = Field(None, ge=0, le=1)
    auto_trading_enabled: Optional[bool] = None
    max_open_positions: Optional[int] = Field(None, ge=1, le=20)
    min_signal_confidence: Optional[float] = Field(None, ge=0, le=1)

class TradingAccountResponse(TradingAccountBase):
    id: int
    user_id: int
    is_active: bool
    total_balance: Decimal
    available_balance: Decimal
    total_pnl: Decimal
    last_sync_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Position schemas
class TradingPositionBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    side: PositionSide
    size: Decimal = Field(..., gt=0)
    entry_price: Decimal = Field(..., gt=0)
    stop_loss: Optional[Decimal] = Field(None, gt=0)
    take_profit: Optional[Decimal] = Field(None, gt=0)
    trailing_stop: bool = False
    trailing_stop_distance: Optional[float] = Field(None, ge=0, le=1)

class TradingPositionCreate(TradingPositionBase):
    account_id: int
    signal_id: Optional[int] = None

class TradingPositionUpdate(BaseModel):
    stop_loss: Optional[Decimal] = Field(None, gt=0)
    take_profit: Optional[Decimal] = Field(None, gt=0)
    trailing_stop: Optional[bool] = None
    trailing_stop_distance: Optional[float] = Field(None, ge=0, le=1)

class TradingPositionResponse(TradingPositionBase):
    id: int
    account_id: int
    signal_id: Optional[int]
    current_price: Optional[Decimal]
    unrealized_pnl: Decimal
    unrealized_pnl_percent: float
    is_open: bool
    opened_at: datetime
    closed_at: Optional[datetime]
    exit_price: Optional[Decimal]
    realized_pnl: Decimal
    realized_pnl_percent: float
    exchange_order_id: Optional[str]
    exchange_position_id: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Order schemas
class TradingOrderBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    order_type: OrderType
    side: OrderSide
    quantity: Decimal = Field(..., gt=0)
    price: Optional[Decimal] = Field(None, gt=0)

class TradingOrderCreate(TradingOrderBase):
    account_id: int
    position_id: Optional[int] = None

class TradingOrderResponse(TradingOrderBase):
    id: int
    account_id: int
    position_id: Optional[int]
    status: OrderStatus
    filled_quantity: Decimal
    average_fill_price: Optional[Decimal]
    exchange_order_id: Optional[str]
    exchange_client_order_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    filled_at: Optional[datetime]
    metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

# Strategy schemas
class TradingStrategyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    strategy_type: TradingStrategy
    parameters: Optional[Dict[str, Any]] = None

class TradingStrategyCreate(TradingStrategyBase):
    account_id: int

class TradingStrategyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    parameters: Optional[Dict[str, Any]] = None

class TradingStrategyResponse(TradingStrategyBase):
    id: int
    account_id: int
    is_active: bool
    total_trades: int
    winning_trades: int
    total_pnl: Decimal
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float
    created_at: datetime
    last_executed_at: Optional[datetime]

    class Config:
        from_attributes = True

# Risk management schemas
class RiskManagementBase(BaseModel):
    max_position_size_usd: Decimal = Field(default=100.0, ge=0)
    max_daily_loss_usd: Decimal = Field(default=50.0, ge=0)
    max_portfolio_risk: float = Field(default=0.05, ge=0, le=1)
    max_correlation: float = Field(default=0.7, ge=0, le=1)
    default_stop_loss_percent: float = Field(default=0.02, ge=0, le=1)
    trailing_stop_enabled: bool = True
    trailing_stop_distance: float = Field(default=0.01, ge=0, le=1)
    risk_per_trade: float = Field(default=0.02, ge=0, le=1)
    max_positions_per_symbol: int = Field(default=1, ge=1, le=10)
    max_total_positions: int = Field(default=5, ge=1, le=20)
    trading_hours_start: str = Field(default="00:00", regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    trading_hours_end: str = Field(default="23:59", regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    weekend_trading: bool = False
    min_volume_usd: Decimal = Field(default=1000000.0, ge=0)
    max_spread_percent: float = Field(default=0.005, ge=0, le=1)

class RiskManagementCreate(RiskManagementBase):
    user_id: int

class RiskManagementUpdate(BaseModel):
    max_position_size_usd: Optional[Decimal] = Field(None, ge=0)
    max_daily_loss_usd: Optional[Decimal] = Field(None, ge=0)
    max_portfolio_risk: Optional[float] = Field(None, ge=0, le=1)
    max_correlation: Optional[float] = Field(None, ge=0, le=1)
    default_stop_loss_percent: Optional[float] = Field(None, ge=0, le=1)
    trailing_stop_enabled: Optional[bool] = None
    trailing_stop_distance: Optional[float] = Field(None, ge=0, le=1)
    risk_per_trade: Optional[float] = Field(None, ge=0, le=1)
    max_positions_per_symbol: Optional[int] = Field(None, ge=1, le=10)
    max_total_positions: Optional[int] = Field(None, ge=1, le=20)
    trading_hours_start: Optional[str] = Field(None, regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    trading_hours_end: Optional[str] = Field(None, regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    weekend_trading: Optional[bool] = None
    min_volume_usd: Optional[Decimal] = Field(None, ge=0)
    max_spread_percent: Optional[float] = Field(None, ge=0, le=1)

class RiskManagementResponse(RiskManagementBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Trading API schemas
class PlaceOrderRequest(BaseModel):
    account_id: int
    symbol: str = Field(..., min_length=1, max_length=20)
    side: OrderSide
    order_type: OrderType
    quantity: Decimal = Field(..., gt=0)
    price: Optional[Decimal] = Field(None, gt=0)
    stop_loss: Optional[Decimal] = Field(None, gt=0)
    take_profit: Optional[Decimal] = Field(None, gt=0)
    time_in_force: str = Field(default="GTC", regex=r"^(GTC|IOC|FOK)$")

class ClosePositionRequest(BaseModel):
    position_id: int
    quantity: Optional[Decimal] = Field(None, gt=0)  # If None, close entire position

class TradingStatsResponse(BaseModel):
    total_positions: int
    open_positions: int
    closed_positions: int
    total_pnl: Decimal
    total_pnl_percent: float
    win_rate: float
    avg_win: Decimal
    avg_loss: Decimal
    max_drawdown: float
    sharpe_ratio: float
    total_trades: int
    winning_trades: int
    losing_trades: int

# Webhook schemas
class ExchangeWebhook(BaseModel):
    exchange: ExchangeType
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime
    signature: Optional[str] = None

# Validation schemas
class AccountValidationRequest(BaseModel):
    account_id: int

class AccountValidationResponse(BaseModel):
    is_valid: bool
    balance: Optional[Decimal] = None
    permissions: Optional[List[str]] = None
    error_message: Optional[str] = None 