"""
Канонический слой ingestion: сырой факт (RawEvent) и версии текста (MessageVersion).

См. docs/DATA_PLANE_MIGRATION.md. Legacy Signal не заменяется на этом этапе.
"""
from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class RawEvent(Base):
    """
    Write-once логически: изменения контента отражаются только через MessageVersion.
    """

    __tablename__ = "raw_events"
    __table_args__ = (
        Index("ix_raw_events_src_chan_seen", "source_type", "channel_id", "first_seen_at"),
        Index("ix_raw_events_content_hash", "content_hash"),
        Index("ix_raw_events_plat_chan", "platform_message_id", "channel_id"),
        UniqueConstraint(
            "channel_id",
            "platform_message_id",
            name="uq_raw_evt_chan_platmsg",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source_type = Column(String(32), nullable=False)
    source_id = Column(String(255), nullable=True)
    channel_id = Column(Integer, ForeignKey("channels.id", ondelete="SET NULL"), nullable=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    platform_message_id = Column(String(128), nullable=True)
    reply_to_message_id = Column(String(128), nullable=True)
    forward_from = Column(JSON, nullable=True)
    raw_payload = Column(JSON, nullable=False)
    raw_text = Column(Text, nullable=True)
    media_refs = Column(JSON, nullable=True)
    content_hash = Column(String(64), nullable=True)
    language = Column(String(16), nullable=True)
    first_seen_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    ingested_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    message_versions = relationship(
        "MessageVersion",
        back_populates="raw_event",
        cascade="all, delete-orphan",
        order_by="MessageVersion.version_no",
    )


class MessageVersion(Base):
    __tablename__ = "message_versions"
    __table_args__ = (
        UniqueConstraint("raw_event_id", "version_no", name="uq_msgver_event_version"),
        Index("ix_message_versions_content_hash", "content_hash"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    raw_event_id = Column(
        BigInteger,
        ForeignKey("raw_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_no = Column(Integer, nullable=False, server_default="1")
    text_snapshot = Column(Text, nullable=True)
    media_snapshot = Column(JSON, nullable=True)
    content_hash = Column(String(64), nullable=True)
    observed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    version_reason = Column(String(32), nullable=False, server_default="initial")

    raw_event = relationship("RawEvent", back_populates="message_versions")
