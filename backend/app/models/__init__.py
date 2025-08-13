"""
This file makes the 'models' directory a Python package and exports all the models.
This allows us to import any model directly from `app.models` and ensures that
SQLAlchemy's Base class knows about all tables when creating the database.
"""

# Сначала импортируем Base, чтобы избежать циклических импортов
from .base import Base, BaseModel

# Затем импортируем модели без зависимостей
from .user import UserRole, SubscriptionPlan, SubscriptionStatus
from .channel import Channel
from .signal import SignalDirection, SignalStatus
from .signal_result import SignalResultStatus
from .subscription import Subscription
from .payment import PaymentStatus

# Затем импортируем модели с зависимостями
from .user import User
from .signal import Signal, TelegramSignal
from .signal_result import SignalResult
from .payment import Payment

# Импортируем торговые модели
from .trading import (
    TradingAccount,
    TradingPosition,
    TradingOrder,
    TradingStrategy,
    RiskManagement,
    # Enums
    ExchangeType,
    OrderType,
    OrderSide,
    OrderStatus,
    PositionSide,
    StrategyType
)

from .performance_metric import PerformanceMetric

# Импортируем остальные модели
from .apikey import APIKey
from .custom_alert import CustomAlert

# Экспортируем все модели для удобного импорта
__all__ = [
    # Base
    "Base",
    "BaseModel",
    
    # User
    "User",
    "UserRole",
    "SubscriptionPlan",
    "SubscriptionStatus",
    
    # Channel
    "Channel",
    
    # Signal
    "Signal",
    "SignalDirection",
    "SignalStatus",
    "TelegramSignal",
    
    # Signal Result
    "SignalResult",
    "SignalResultStatus",
    
    # Subscription
    "Subscription",
    
    # Trading
    "TradingAccount",
    "TradingPosition",
    "TradingOrder",
    "TradingStrategy",
    "RiskManagement",
    "ExchangeType",
    "OrderType",
    "OrderSide",
    "OrderStatus",
    "PositionSide",
    "StrategyType",
    
    # Performance
    "PerformanceMetric",
    
    # Other models
    "APIKey",
    "CustomAlert",
    "Payment",
    "PaymentStatus"
]