"""Каталог execution models для расчёта canonical outcomes (data plane фаза 10)."""
from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class ExecutionModel(Base):
    """
    Семантика fill/slippage/fee/expiry — JSON-политики (v0); расширение без миграции схемы.
    Ключ `model_key` стабилен в коде и отчётах (см. docs/MARKET_OUTCOME_POLICY.md §6).
    """

    __tablename__ = "execution_models"
    __table_args__ = (UniqueConstraint("model_key", name="uq_execution_models_key"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_key = Column(String(64), nullable=False)
    display_name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    fill_rule = Column(JSON, nullable=True)
    slippage_policy = Column(JSON, nullable=True)
    fee_policy = Column(JSON, nullable=True)
    expiry_policy = Column(JSON, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="true")
    sort_order = Column(Integer, nullable=False, server_default="0")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    signal_outcomes = relationship("SignalOutcome", back_populates="execution_model")
