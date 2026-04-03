"""
Custom Alert Model - Database model for user custom alerts
"""
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Float, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum

from .base import BaseModel

class AlertType(str, Enum):
    """Типы уведомлений"""
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PRICE_CHANGE = "price_change"
    VOLUME_SPIKE = "volume_spike"
    TECHNICAL_INDICATOR = "technical_indicator"
    CUSTOM_EVENT = "custom_event"

class AlertStatus(str, Enum):
    """Статусы уведомлений"""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class CustomAlert(BaseModel):
    """
    Модель для хранения пользовательских уведомлений
    """
    __tablename__ = "custom_alerts"
    
    # Основные поля
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    alert_type = Column(String(50), nullable=False)  # Один из AlertType
    status = Column(String(20), default=AlertStatus.ACTIVE.value, nullable=False)
    
    # Параметры уведомления (symbol/condition — legacy; для Pro API используются conditions + notification_methods)
    symbol = Column(String(50), nullable=True)
    condition = Column(JSON, nullable=True)
    conditions = Column(JSON, nullable=True)
    notification_methods = Column(JSON, nullable=True)
    webhook_url = Column(String(512), nullable=True)
    triggered_count = Column(Integer, default=0, nullable=False)

    # Настройки уведомлений
    is_active = Column(Boolean, default=True)
    is_recurring = Column(Boolean, default=False)  # Повторяющееся уведомление
    
    # Временные метки
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Владелец уведомления
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="custom_alerts")
    
    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<CustomAlert(id={self.id}, name='{self.name}', type='{self.alert_type}')>"
    
    @property
    def is_expired(self) -> bool:
        """Проверяет, истекло ли уведомление"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def can_trigger(self) -> bool:
        """Можно ли сработать уведомлению"""
        st = self.status
        if isinstance(st, AlertStatus):
            st_ok = st == AlertStatus.ACTIVE
        else:
            st_ok = st == AlertStatus.ACTIVE.value
        return self.is_active and st_ok and not self.is_expired
