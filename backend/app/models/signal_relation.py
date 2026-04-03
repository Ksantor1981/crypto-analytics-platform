"""SignalRelation — связь между каноническими сигналами (duplicate / update / close)."""
from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class SignalRelation(Base):
    __tablename__ = "signal_relations"
    __table_args__ = (
        UniqueConstraint(
            "from_normalized_signal_id",
            "to_normalized_signal_id",
            "relation_type",
            name="uq_sigrel_from_to_type",
        ),
        Index("ix_sigrel_from_norm_id", "from_normalized_signal_id"),
        Index("ix_sigrel_to_norm_id", "to_normalized_signal_id"),
        Index("ix_sigrel_relation_type", "relation_type"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    from_normalized_signal_id = Column(
        BigInteger,
        ForeignKey("normalized_signals.id", ondelete="CASCADE"),
        nullable=False,
    )
    to_normalized_signal_id = Column(
        BigInteger,
        ForeignKey("normalized_signals.id", ondelete="CASCADE"),
        nullable=False,
    )
    relation_type = Column(String(32), nullable=False)
    relation_source = Column(String(32), nullable=False, server_default="manual")
    confidence = Column(Float, nullable=True)
    relation_meta = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    from_signal = relationship(
        "NormalizedSignal",
        foreign_keys=[from_normalized_signal_id],
        back_populates="outgoing_relations",
    )
    to_signal = relationship(
        "NormalizedSignal",
        foreign_keys=[to_normalized_signal_id],
        back_populates="incoming_relations",
    )
