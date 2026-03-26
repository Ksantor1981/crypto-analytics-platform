"""Merge Alembic heads for signal dedup and market data branches.

Revision ID: 9f1a2b3c4d5e
Revises: d1e2f3a4b5c6, f4a5b6c7d8e9
Create Date: 2026-03-26 16:10:00.000000
"""

from typing import Sequence, Union


revision: str = "9f1a2b3c4d5e"
down_revision: Union[str, Sequence[str], None] = ("d1e2f3a4b5c6", "f4a5b6c7d8e9")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Merge revision: schema changes are in parent branches.
    pass


def downgrade() -> None:
    # Split merge point back into two independent heads.
    pass
