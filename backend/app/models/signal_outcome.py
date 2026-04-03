"""SignalOutcome — расчёт исхода по паре (NormalizedSignal, ExecutionModel), фаза 11."""
from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class SignalOutcome(Base):
    """
    Одна строка на (normalized_signal, execution_model).
    Расчёт полей — отдельный worker (пока допускается только PENDING + ручные правки admin).
    """

    __tablename__ = "signal_outcomes"
    __table_args__ = (
        UniqueConstraint(
            "normalized_signal_id",
            "execution_model_id",
            name="uq_signal_outcomes_norm_exec",
        ),
        Index("ix_signal_outcomes_norm_id", "normalized_signal_id"),
        Index("ix_signal_outcomes_exec_id", "execution_model_id"),
        Index("ix_signal_outcomes_status", "outcome_status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    normalized_signal_id = Column(
        BigInteger,
        ForeignKey("normalized_signals.id", ondelete="CASCADE"),
        nullable=False,
    )
    execution_model_id = Column(
        Integer,
        ForeignKey("execution_models.id", ondelete="RESTRICT"),
        nullable=False,
    )
    outcome_status = Column(String(32), nullable=False, default="PENDING", server_default="PENDING")

    entry_reached = Column(Boolean, nullable=True)
    entry_fill_price = Column(Numeric(20, 8), nullable=True)
    tp_hits = Column(JSON, nullable=True)
    sl_hit = Column(Boolean, nullable=True)
    expiry_hit = Column(Boolean, nullable=True)
    mfe = Column(Numeric(20, 8), nullable=True)
    mae = Column(Numeric(20, 8), nullable=True)
    time_to_entry_sec = Column(Integer, nullable=True)
    time_to_outcome_sec = Column(Integer, nullable=True)
    calculated_at = Column(DateTime(timezone=True), nullable=True)
    market_data_version = Column(String(64), nullable=True)
    policy_ref = Column(String(128), nullable=True)
    error_detail = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    normalized_signal = relationship("NormalizedSignal", back_populates="signal_outcomes")
    execution_model = relationship("ExecutionModel", back_populates="signal_outcomes")
