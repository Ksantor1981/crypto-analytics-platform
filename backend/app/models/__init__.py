"""
Database models initialization
"""
from .base import BaseModel
from .user import User
from .channel import Channel
from .signal import Signal, TelegramSignal, SignalDirection, SignalStatus
from .subscription import Subscription
from .payment import Payment
from .performance_metric import PerformanceMetric
from .api_key import APIKey

# Ensure all models are imported for Alembic auto-generation
__all__ = [
    "BaseModel",
    "User", 
    "Channel",
    "Signal",
    "TelegramSignal",
    "SignalDirection",
    "SignalStatus",
    "Subscription",
    "Payment", 
    "PerformanceMetric",
    "APIKey"
] 