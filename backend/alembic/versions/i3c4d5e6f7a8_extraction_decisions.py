"""extraction_decisions — итог классификации контура (data plane phase 6)

Revision ID: i3c4d5e6f7a8
Revises: h2b3c4d5e6f7
Create Date: 2026-04-04

См. docs/DOMAIN_GLOSSARY_CANONICAL.md (ExtractionDecision)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "i3c4d5e6f7a8"
down_revision: Union[str, None] = "h2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "extraction_decisions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("extraction_id", sa.BigInteger(), nullable=False),
        sa.Column("raw_event_id", sa.BigInteger(), nullable=False),
        sa.Column("decision_type", sa.String(length=32), nullable=False),
        sa.Column(
            "decision_source",
            sa.String(length=32),
            nullable=False,
            server_default="rules_v0",
        ),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("rationale", sa.JSON(), nullable=True),
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
        sa.ForeignKeyConstraint(["extraction_id"], ["extractions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["raw_event_id"], ["raw_events.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("extraction_id", name="uq_extr_decision_extraction"),
    )
    op.create_index(
        "ix_extr_decisions_raw_event_id",
        "extraction_decisions",
        ["raw_event_id"],
        unique=False,
    )
    op.create_index(
        "ix_extr_decisions_decision_type",
        "extraction_decisions",
        ["decision_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_extr_decisions_decision_type", table_name="extraction_decisions")
    op.drop_index("ix_extr_decisions_raw_event_id", table_name="extraction_decisions")
    op.drop_table("extraction_decisions")
