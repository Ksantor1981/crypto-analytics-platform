"""Канонический слой extraction (результат парсера по MessageVersion)."""
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


class Extraction(Base):
    """
    Результат экстрактора для конкретной версии сообщения.
    Уникальность (message_version_id, extractor_name, extractor_version) — идемпотентный прогон.
    """

    __tablename__ = "extractions"
    __table_args__ = (
        UniqueConstraint(
            "message_version_id",
            "extractor_name",
            "extractor_version",
            name="uq_extr_mv_extractor",
        ),
        Index("ix_extractions_raw_event_id", "raw_event_id"),
        Index("ix_extractions_message_version_id", "message_version_id"),
        Index("ix_extractions_classification_status", "classification_status"),
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
    extractor_name = Column(String(64), nullable=False)
    extractor_version = Column(String(32), nullable=False)
    classification_status = Column(String(32), nullable=False)
    confidence = Column(Float, nullable=True)
    extracted_fields = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    raw_event = relationship("RawEvent", backref="extractions")
    message_version = relationship("MessageVersion", backref="extractions")
    decision = relationship(
        "ExtractionDecision",
        back_populates="extraction",
        uselist=False,
        cascade="all, delete-orphan",
    )
    normalized_signal = relationship(
        "NormalizedSignal",
        back_populates="extraction",
        uselist=False,
        cascade="all, delete-orphan",
    )
