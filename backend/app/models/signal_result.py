"""
SignalResult model stub - временная заглушка для тестирования
TODO: Заменить на реальную реализацию ML-пайплайна
"""
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Enum, JSON, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import BaseModel

class SignalResultStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class SignalResult(BaseModel):
    """
    Заглушка для модели результатов сигналов
    """
    __tablename__ = "signal_results"
    
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=False, unique=True, index=True)
    signal = relationship("Signal", back_populates="result")
    
    # Основные метрики
    status = Column(Enum(SignalResultStatus), default=SignalResultStatus.PENDING, nullable=False)
    pnl = Column(Numeric(15, 8), nullable=True)  # Прибыль/убыток в базовой валюте
    pnl_percent = Column(Float, nullable=True)    # Прибыль/убыток в процентах
    
    # Временные метрики
    entry_time = Column(DateTime(timezone=True), nullable=True)
    exit_time = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    
    # ML-метрики (заглушки)
    confidence_score = Column(Float, nullable=True)
    model_version = Column(String(50), nullable=True)
    ml_metadata = Column(JSON, nullable=True)
    
    # Дополнительные поля
    notes = Column(String(500), nullable=True)
    
    def __repr__(self):
        return f"<SignalResult(signal_id={self.signal_id}, status={self.status}, pnl={self.pnl})>"
    
    @classmethod
    def get_by_signal_id(cls, db, signal_id):
        """Получить результат по ID сигнала"""
        return db.query(cls).filter(cls.signal_id == signal_id).first()
    
    def update_status(self, db, status, commit=True):
        """Обновить статус результата"""
        self.status = status
        if commit:
            db.commit()
            db.refresh(self)
        return self
