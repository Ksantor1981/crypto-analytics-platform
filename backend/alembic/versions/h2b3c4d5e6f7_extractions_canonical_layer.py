"""extractions — канонический слой парсинга (data plane phase 5)

Revision ID: h2b3c4d5e6f7
Revises: g1a2b3c4d5e6
Create Date: 2026-04-04

См. docs/DATA_PLANE_MIGRATION.md, docs/DOMAIN_GLOSSARY_CANONICAL.md
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "h2b3c4d5e6f7"
down_revision: Union[str, None] = "g1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "extractions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("raw_event_id", sa.BigInteger(), nullable=False),
        sa.Column("message_version_id", sa.BigInteger(), nullable=False),
        sa.Column("extractor_name", sa.String(length=64), nullable=False),
        sa.Column("extractor_version", sa.String(length=32), nullable=False),
        sa.Column("classification_status", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("extracted_fields", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["raw_event_id"], ["raw_events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["message_version_id"],
            ["message_versions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "message_version_id",
            "extractor_name",
            "extractor_version",
            name="uq_extr_mv_extractor",
        ),
    )
    op.create_index("ix_extractions_raw_event_id", "extractions", ["raw_event_id"], unique=False)
    op.create_index(
        "ix_extractions_message_version_id",
        "extractions",
        ["message_version_id"],
        unique=False,
    )
    op.create_index(
        "ix_extractions_classification_status",
        "extractions",
        ["classification_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_extractions_classification_status", table_name="extractions")
    op.drop_index("ix_extractions_message_version_id", table_name="extractions")
    op.drop_index("ix_extractions_raw_event_id", table_name="extractions")
    op.drop_table("extractions")
