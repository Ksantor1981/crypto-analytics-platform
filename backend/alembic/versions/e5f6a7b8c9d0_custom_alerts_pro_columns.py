"""custom_alerts: Pro API columns (conditions, webhook, triggered_count)

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-04-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("custom_alerts", sa.Column("conditions", sa.JSON(), nullable=True))
    op.add_column("custom_alerts", sa.Column("notification_methods", sa.JSON(), nullable=True))
    op.add_column("custom_alerts", sa.Column("webhook_url", sa.String(length=512), nullable=True))
    op.add_column(
        "custom_alerts",
        sa.Column("triggered_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.alter_column(
        "custom_alerts",
        "symbol",
        existing_type=sa.String(length=50),
        nullable=True,
    )
    op.alter_column(
        "custom_alerts",
        "condition",
        existing_type=sa.JSON(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "custom_alerts",
        "condition",
        existing_type=sa.JSON(),
        nullable=False,
    )
    op.alter_column(
        "custom_alerts",
        "symbol",
        existing_type=sa.String(length=50),
        nullable=False,
    )
    op.drop_column("custom_alerts", "triggered_count")
    op.drop_column("custom_alerts", "webhook_url")
    op.drop_column("custom_alerts", "notification_methods")
    op.drop_column("custom_alerts", "conditions")
