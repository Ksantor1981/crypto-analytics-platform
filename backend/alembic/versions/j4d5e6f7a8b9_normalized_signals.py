"""normalized_signals — каноническое торговое намерение (data plane phase 8)

Revision ID: j4d5e6f7a8b9
Revises: i3c4d5e6f7a8
Create Date: 2026-04-04

См. docs/DOMAIN_GLOSSARY_CANONICAL.md (NormalizedSignal)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "j4d5e6f7a8b9"
down_revision: Union[str, None] = "i3c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "normalized_signals",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("raw_event_id", sa.BigInteger(), nullable=False),
        sa.Column("message_version_id", sa.BigInteger(), nullable=False),
        sa.Column("extraction_id", sa.BigInteger(), nullable=False),
        sa.Column("legacy_signal_id", sa.Integer(), nullable=True),
        sa.Column("asset", sa.String(length=64), nullable=False),
        sa.Column("direction", sa.String(length=16), nullable=False),
        sa.Column("entry_price", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("take_profit", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("stop_loss", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("entry_zone_low", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("entry_zone_high", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column(
            "trading_lifecycle_status",
            sa.String(length=32),
            nullable=False,
            server_default="PENDING_ENTRY",
        ),
        sa.Column(
            "relation_status",
            sa.String(length=32),
            nullable=False,
            server_default="UNLINKED",
        ),
        sa.Column("provenance", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["raw_event_id"], ["raw_events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["message_version_id"], ["message_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["extraction_id"], ["extractions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["legacy_signal_id"], ["signals.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("extraction_id", name="uq_norm_sig_extraction"),
    )
    op.create_index(
        "ix_normalized_signals_raw_event_id",
        "normalized_signals",
        ["raw_event_id"],
        unique=False,
    )
    op.create_index(
        "ix_normalized_signals_legacy_signal_id",
        "normalized_signals",
        ["legacy_signal_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_normalized_signals_legacy_signal_id", table_name="normalized_signals")
    op.drop_index("ix_normalized_signals_raw_event_id", table_name="normalized_signals")
    op.drop_table("normalized_signals")
