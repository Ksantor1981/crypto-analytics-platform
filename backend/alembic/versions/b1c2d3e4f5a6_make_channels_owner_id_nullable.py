"""Make channels.owner_id nullable for system-owned sources.

Revision ID: b1c2d3e4f5a6
Revises: a7b8c9d0e1f2
Create Date: 2026-03-26 17:20:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("channels", "owner_id", nullable=True)


def downgrade() -> None:
    op.alter_column("channels", "owner_id", nullable=False)
