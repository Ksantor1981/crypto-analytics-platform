"""Add missing signals.ml_prediction JSON column.

Revision ID: c3d4e5f6a7b8
Revises: b1c2d3e4f5a6
Create Date: 2026-03-26 17:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("ALTER TABLE signals ADD COLUMN IF NOT EXISTS ml_prediction JSON"))


def downgrade() -> None:
    op.execute(sa.text("ALTER TABLE signals DROP COLUMN IF EXISTS ml_prediction"))
