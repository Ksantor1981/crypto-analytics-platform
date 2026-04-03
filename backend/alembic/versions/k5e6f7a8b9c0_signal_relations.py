"""signal_relations — связи между normalized_signals (data plane phase 7)

Revision ID: k5e6f7a8b9c0
Revises: j4d5e6f7a8b9
Create Date: 2026-04-04

См. docs/DOMAIN_GLOSSARY_CANONICAL.md (SignalRelation)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "k5e6f7a8b9c0"
down_revision: Union[str, None] = "j4d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "signal_relations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("from_normalized_signal_id", sa.BigInteger(), nullable=False),
        sa.Column("to_normalized_signal_id", sa.BigInteger(), nullable=False),
        sa.Column("relation_type", sa.String(length=32), nullable=False),
        sa.Column(
            "relation_source",
            sa.String(length=32),
            nullable=False,
            server_default="manual",
        ),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("relation_meta", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["from_normalized_signal_id"],
            ["normalized_signals.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["to_normalized_signal_id"],
            ["normalized_signals.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "from_normalized_signal_id",
            "to_normalized_signal_id",
            "relation_type",
            name="uq_sigrel_from_to_type",
        ),
    )
    op.create_index(
        "ix_sigrel_from_norm_id",
        "signal_relations",
        ["from_normalized_signal_id"],
        unique=False,
    )
    op.create_index(
        "ix_sigrel_to_norm_id",
        "signal_relations",
        ["to_normalized_signal_id"],
        unique=False,
    )
    op.create_index(
        "ix_sigrel_relation_type",
        "signal_relations",
        ["relation_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_sigrel_relation_type", table_name="signal_relations")
    op.drop_index("ix_sigrel_to_norm_id", table_name="signal_relations")
    op.drop_index("ix_sigrel_from_norm_id", table_name="signal_relations")
    op.drop_table("signal_relations")
