"""raw_events + message_versions (canonical ingestion layer)

Revision ID: f8e9a0b1c2d3
Revises: e5f6a7b8c9d0
Create Date: 2026-04-04

См. docs/DATA_PLANE_MIGRATION.md
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f8e9a0b1c2d3"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "raw_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=True),
        sa.Column("channel_id", sa.Integer(), nullable=True),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("platform_message_id", sa.String(length=128), nullable=True),
        sa.Column("reply_to_message_id", sa.String(length=128), nullable=True),
        sa.Column("forward_from", sa.JSON(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("media_refs", sa.JSON(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("channel_id", "platform_message_id", name="uq_raw_evt_chan_platmsg"),
    )
    op.create_index("ix_raw_events_channel_id", "raw_events", ["channel_id"], unique=False)
    op.create_index("ix_raw_events_author_id", "raw_events", ["author_id"], unique=False)
    op.create_index(
        "ix_raw_events_src_chan_seen",
        "raw_events",
        ["source_type", "channel_id", "first_seen_at"],
        unique=False,
    )
    op.create_index("ix_raw_events_content_hash", "raw_events", ["content_hash"], unique=False)
    op.create_index(
        "ix_raw_events_plat_chan",
        "raw_events",
        ["platform_message_id", "channel_id"],
        unique=False,
    )

    op.create_table(
        "message_versions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("raw_event_id", sa.BigInteger(), nullable=False),
        sa.Column("version_no", sa.Integer(), server_default="1", nullable=False),
        sa.Column("text_snapshot", sa.Text(), nullable=True),
        sa.Column("media_snapshot", sa.JSON(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column(
            "observed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "version_reason",
            sa.String(length=32),
            server_default="initial",
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["raw_event_id"], ["raw_events.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("raw_event_id", "version_no", name="uq_msgver_event_version"),
    )
    op.create_index(
        "ix_message_versions_raw_event_id",
        "message_versions",
        ["raw_event_id"],
        unique=False,
    )
    op.create_index(
        "ix_message_versions_content_hash",
        "message_versions",
        ["content_hash"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_message_versions_content_hash", table_name="message_versions")
    op.drop_index("ix_message_versions_raw_event_id", table_name="message_versions")
    op.drop_table("message_versions")
    op.drop_index("ix_raw_events_plat_chan", table_name="raw_events")
    op.drop_index("ix_raw_events_content_hash", table_name="raw_events")
    op.drop_index("ix_raw_events_src_chan_seen", table_name="raw_events")
    op.drop_index("ix_raw_events_author_id", table_name="raw_events")
    op.drop_index("ix_raw_events_channel_id", table_name="raw_events")
    op.drop_table("raw_events")
