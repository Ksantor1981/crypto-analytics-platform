"""signal_outcomes — результат по рынку (normalized × execution_model), фаза 11

Revision ID: m7b8c9d0e1f2
Revises: l6f7a8b9c0d1
Create Date: 2026-04-04

См. docs/DATA_PLANE_MIGRATION.md, docs/MARKET_OUTCOME_POLICY.md
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "m7b8c9d0e1f2"
down_revision: Union[str, None] = "l6f7a8b9c0d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "signal_outcomes",
        # Integer PK: совместимость SQLite autoincrement; объёма достаточно до фазы шардирования
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("normalized_signal_id", sa.BigInteger(), nullable=False),
        sa.Column("execution_model_id", sa.Integer(), nullable=False),
        sa.Column(
            "outcome_status",
            sa.String(length=32),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("entry_reached", sa.Boolean(), nullable=True),
        sa.Column("entry_fill_price", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("tp_hits", sa.JSON(), nullable=True),
        sa.Column("sl_hit", sa.Boolean(), nullable=True),
        sa.Column("expiry_hit", sa.Boolean(), nullable=True),
        sa.Column("mfe", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("mae", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("time_to_entry_sec", sa.Integer(), nullable=True),
        sa.Column("time_to_outcome_sec", sa.Integer(), nullable=True),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("market_data_version", sa.String(length=64), nullable=True),
        sa.Column("policy_ref", sa.String(length=128), nullable=True),
        sa.Column("error_detail", sa.JSON(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["execution_model_id"],
            ["execution_models.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["normalized_signal_id"],
            ["normalized_signals.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "normalized_signal_id",
            "execution_model_id",
            name="uq_signal_outcomes_norm_exec",
        ),
    )
    op.create_index(
        "ix_signal_outcomes_norm_id",
        "signal_outcomes",
        ["normalized_signal_id"],
        unique=False,
    )
    op.create_index(
        "ix_signal_outcomes_exec_id",
        "signal_outcomes",
        ["execution_model_id"],
        unique=False,
    )
    op.create_index(
        "ix_signal_outcomes_status",
        "signal_outcomes",
        ["outcome_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_signal_outcomes_status", table_name="signal_outcomes")
    op.drop_index("ix_signal_outcomes_exec_id", table_name="signal_outcomes")
    op.drop_index("ix_signal_outcomes_norm_id", table_name="signal_outcomes")
    op.drop_table("signal_outcomes")
