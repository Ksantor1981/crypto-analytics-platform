"""Add channel auto-discovery and health fields

Revision ID: c7d8e9f0a1b2
Revises: b2c3d4e5f6g7
Create Date: 2026-03-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7d8e9f0a1b2'
down_revision: Union[str, None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('channels', sa.Column('discovered_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('channels', sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('channels', sa.Column('last_new_signal_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('channels', sa.Column('is_candidate', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('channels', sa.Column('disabled_reason', sa.String(length=255), nullable=True))

    op.create_index('ix_channels_platform_active', 'channels', ['platform', 'is_active'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_channels_platform_active', table_name='channels')
    op.drop_column('channels', 'disabled_reason')
    op.drop_column('channels', 'is_candidate')
    op.drop_column('channels', 'last_new_signal_at')
    op.drop_column('channels', 'last_checked_at')
    op.drop_column('channels', 'discovered_at')

