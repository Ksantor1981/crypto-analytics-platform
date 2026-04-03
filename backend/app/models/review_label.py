"""Ручная разметка для Review Console (data plane фаза 4)."""
from __future__ import annotations

from sqlalchemy import BigInteger, Column, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ReviewLabel(BaseModel):
    __tablename__ = "review_labels"

    raw_event_id = Column(
        BigInteger,
        ForeignKey("raw_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewer_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    reviewer_name = Column(String(128), nullable=True)
    label_type = Column(String(32), nullable=False, index=True)
    corrected_fields = Column(JSON, nullable=True)
    linked_signal_id = Column(Integer, ForeignKey("signals.id", ondelete="SET NULL"), nullable=True, index=True)
    notes = Column(Text, nullable=True)

    raw_event = relationship("RawEvent", backref="review_labels")
    reviewer_user = relationship("User", foreign_keys=[reviewer_user_id])
