"""ExtractionDecision — итог классификации по строке extraction (фаза 6 data plane)."""
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


class ExtractionDecision(Base):
    """
    Одна строка на extraction (rules_v0 или manual override).
    decision_type: signal | update | close | commentary | duplicate | noise | unresolved
    """

    __tablename__ = "extraction_decisions"
    __table_args__ = (
        UniqueConstraint("extraction_id", name="uq_extr_decision_extraction"),
        Index("ix_extr_decisions_raw_event_id", "raw_event_id"),
        Index("ix_extr_decisions_decision_type", "decision_type"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    extraction_id = Column(
        BigInteger,
        ForeignKey("extractions.id", ondelete="CASCADE"),
        nullable=False,
    )
    raw_event_id = Column(
        BigInteger,
        ForeignKey("raw_events.id", ondelete="CASCADE"),
        nullable=False,
    )
    decision_type = Column(String(32), nullable=False)
    decision_source = Column(String(32), nullable=False, server_default="rules_v0")
    confidence = Column(Float, nullable=True)
    rationale = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    extraction = relationship("Extraction", back_populates="decision")
    raw_event = relationship("RawEvent", backref="extraction_decisions")
