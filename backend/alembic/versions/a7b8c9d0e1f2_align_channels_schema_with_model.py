"""Align channels table schema with ORM model expectations.

Revision ID: a7b8c9d0e1f2
Revises: 9f1a2b3c4d5e
Create Date: 2026-03-26 16:55:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, None] = "9f1a2b3c4d5e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(c["name"] == column for c in inspector.get_columns(table))


def _has_index(table: str, index: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(i["name"] == index for i in inspector.get_indexes(table))


def _has_unique_constraint(table: str, name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(c["name"] == name for c in inspector.get_unique_constraints(table))


def upgrade() -> None:
    # Add missing columns used by app.models.channel.Channel.
    # Use IF NOT EXISTS to stay safe across partially-aligned databases.
    op.execute(sa.text("ALTER TABLE channels ADD COLUMN IF NOT EXISTS username VARCHAR(100)"))
    op.execute(sa.text("ALTER TABLE channels ADD COLUMN IF NOT EXISTS subscribers_count INTEGER"))
    op.execute(sa.text("ALTER TABLE channels ADD COLUMN IF NOT EXISTS priority INTEGER"))
    op.execute(sa.text("ALTER TABLE channels ADD COLUMN IF NOT EXISTS expected_accuracy VARCHAR(50)"))
    op.execute(sa.text("ALTER TABLE channels ADD COLUMN IF NOT EXISTS status VARCHAR(50)"))
    op.execute(sa.text("UPDATE channels SET priority = 1 WHERE priority IS NULL"))
    op.execute(sa.text("UPDATE channels SET status = 'active' WHERE status IS NULL"))

    # Backfill username for existing rows and enforce constraints used by ORM.
    op.execute(
        sa.text(
            """
            UPDATE channels
            SET username = COALESCE(NULLIF(username, ''), lower(regexp_replace(name, '[^a-zA-Z0-9_]+', '_', 'g')) || '_' || id::text)
            WHERE username IS NULL OR username = ''
            """
        )
    )
    op.alter_column("channels", "priority", nullable=False)
    op.alter_column("channels", "status", nullable=False)
    op.alter_column("channels", "username", nullable=False)
    op.alter_column("channels", "owner_id", nullable=True)

    if not _has_unique_constraint("channels", "uq_channels_username"):
        op.create_unique_constraint("uq_channels_username", "channels", ["username"])
    if not _has_index("channels", "ix_channels_username"):
        op.create_index("ix_channels_username", "channels", ["username"], unique=False)


def downgrade() -> None:
    if _has_index("channels", "ix_channels_username"):
        op.drop_index("ix_channels_username", table_name="channels")
    if _has_unique_constraint("channels", "uq_channels_username"):
        op.drop_constraint("uq_channels_username", "channels", type_="unique")

    if _has_column("channels", "status"):
        op.drop_column("channels", "status")
    if _has_column("channels", "expected_accuracy"):
        op.drop_column("channels", "expected_accuracy")
    if _has_column("channels", "priority"):
        op.drop_column("channels", "priority")
    if _has_column("channels", "subscribers_count"):
        op.drop_column("channels", "subscribers_count")
    if _has_column("channels", "username"):
        op.drop_column("channels", "username")
