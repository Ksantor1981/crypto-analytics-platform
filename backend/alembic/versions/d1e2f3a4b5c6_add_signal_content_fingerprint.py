"""Add content_fingerprint to signals for stable dedup

Revision ID: d1e2f3a4b5c6
Revises: c7d8e9f0a1b2
Create Date: 2026-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, None] = "c7d8e9f0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "signals",
        sa.Column("content_fingerprint", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_signals_content_fingerprint",
        "signals",
        ["content_fingerprint"],
        unique=False,
    )
    op.create_index(
        "ix_signals_channel_fingerprint",
        "signals",
        ["channel_id", "content_fingerprint"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_signals_channel_fingerprint", table_name="signals")
    op.drop_index("ix_signals_content_fingerprint", table_name="signals")
    op.drop_column("signals", "content_fingerprint")
