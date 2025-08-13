from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta

from .base import BaseModel

class APIKey(BaseModel):
    """
    Модель для хранения API-ключей пользователей
    """
    __tablename__ = "api_keys"
    
    # Основные поля
    name = Column(String(100), nullable=False)
    key = Column(String(255), nullable=False, unique=True, index=True)
    secret = Column(String(255), nullable=True)  # Зашифрованный секрет
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Владелец ключа
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="api_keys")
    
    # Разрешения
    permissions = Column(String(500), nullable=True)  # JSON-строка с разрешениями
    
    # IP-ограничения
    allowed_ips = Column(String(500), nullable=True)  # JSON-массив разрешенных IP
    
    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, name='{self.name}', user_id={self.user_id})>"
    
    @property
    def is_expired(self) -> bool:
        """Проверяет, истек ли срок действия ключа"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Проверяет, действителен ли ключ"""
        return self.is_active and not self.is_expired
