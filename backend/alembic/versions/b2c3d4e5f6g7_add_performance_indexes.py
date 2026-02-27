"""Add performance indexes for signals and channels

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-28

"""
from typing import Sequence, Union

from alembic import op

revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Composite index: signals by channel + created_at (list/filter queries)
    op.create_index(
        'ix_signals_channel_created',
        'signals',
        ['channel_id', 'created_at'],
        unique=False,
    )
    # Index: signals by status (filter PENDING, etc.)
    op.create_index(
        'ix_signals_status',
        'signals',
        ['status'],
        unique=False,
    )
    # Index: channels by accuracy (realtime/antirealtime ranking)
    op.create_index(
        'ix_channels_accuracy',
        'channels',
        ['accuracy'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_channels_accuracy', table_name='channels')
    op.drop_index('ix_signals_status', table_name='signals')
    op.drop_index('ix_signals_channel_created', table_name='signals')
