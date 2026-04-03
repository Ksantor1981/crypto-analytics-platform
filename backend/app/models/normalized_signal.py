"""NormalizedSignal — каноническое представление намерения (data plane фаза 8)."""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import (
    BigInteger,
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


class NormalizedSignal(Base):
    """
    Одна строка на extraction при материализации (uq_norm_sig_extraction).
    Цены — Numeric; связь с legacy signals опциональна.
    """

    __tablename__ = "normalized_signals"
    __table_args__ = (
        UniqueConstraint("extraction_id", name="uq_norm_sig_extraction"),
        Index("ix_normalized_signals_raw_event_id", "raw_event_id"),
        Index("ix_normalized_signals_legacy_signal_id", "legacy_signal_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    raw_event_id = Column(
        BigInteger,
        ForeignKey("raw_events.id", ondelete="CASCADE"),
        nullable=False,
    )
    message_version_id = Column(
        BigInteger,
        ForeignKey("message_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    extraction_id = Column(
        BigInteger,
        ForeignKey("extractions.id", ondelete="CASCADE"),
        nullable=False,
    )
    legacy_signal_id = Column(
        Integer,
        ForeignKey("signals.id", ondelete="SET NULL"),
        nullable=True,
    )

    asset = Column(String(64), nullable=False)
    direction = Column(String(16), nullable=False)
    entry_price = Column(Numeric(20, 8), nullable=False)
    take_profit = Column(Numeric(20, 8), nullable=True)
    stop_loss = Column(Numeric(20, 8), nullable=True)
    entry_zone_low = Column(Numeric(20, 8), nullable=True)
    entry_zone_high = Column(Numeric(20, 8), nullable=True)

    trading_lifecycle_status = Column(String(32), nullable=False, default="PENDING_ENTRY")
    relation_status = Column(String(32), nullable=False, default="UNLINKED")
    provenance = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    raw_event = relationship("RawEvent", backref="normalized_signals")
    message_version = relationship("MessageVersion", backref="normalized_signals")
    extraction = relationship("Extraction", back_populates="normalized_signal")
    legacy_signal = relationship("Signal", foreign_keys=[legacy_signal_id])
    outgoing_relations = relationship(
        "SignalRelation",
        foreign_keys="SignalRelation.from_normalized_signal_id",
        back_populates="from_signal",
    )
    incoming_relations = relationship(
        "SignalRelation",
        foreign_keys="SignalRelation.to_normalized_signal_id",
        back_populates="to_signal",
    )
    signal_outcomes = relationship(
        "SignalOutcome",
        back_populates="normalized_signal",
        cascade="all, delete-orphan",
    )

    @staticmethod
    def numeric_or_none(v: Any) -> Optional[Decimal]:
        if v is None:
            return None
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))
