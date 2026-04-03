"""execution_models — каталог моделей исполнения (data plane phase 10)

Revision ID: l6f7a8b9c0d1
Revises: k5e6f7a8b9c0
Create Date: 2026-04-04

См. docs/DATA_PLANE_MIGRATION.md, docs/MARKET_OUTCOME_POLICY.md §6
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "l6f7a8b9c0d1"
down_revision: Union[str, None] = "k5e6f7a8b9c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "execution_models",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("model_key", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("fill_rule", sa.JSON(), nullable=True),
        sa.Column("slippage_policy", sa.JSON(), nullable=True),
        sa.Column("fee_policy", sa.JSON(), nullable=True),
        sa.Column("expiry_policy", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("model_key", name="uq_execution_models_key"),
    )

    op.create_index("ix_execution_models_model_key", "execution_models", ["model_key"], unique=False)
    op.create_index("ix_execution_models_is_active", "execution_models", ["is_active"], unique=False)

    seed = sa.table(
        "execution_models",
        sa.column("model_key", sa.String),
        sa.column("display_name", sa.String),
        sa.column("description", sa.Text),
        sa.column("fill_rule", sa.JSON),
        sa.column("slippage_policy", sa.JSON),
        sa.column("fee_policy", sa.JSON),
        sa.column("expiry_policy", sa.JSON),
        sa.column("is_active", sa.Boolean),
        sa.column("sort_order", sa.Integer),
    )
    op.bulk_insert(
        seed,
        [
            {
                "model_key": "market_on_publish",
                "display_name": "Market on publish",
                "description": "Вход по цене на момент публикации (см. MARKET_OUTCOME_POLICY §4, §6).",
                "fill_rule": {"variant": "price_at_publish", "policy_ref": "MARKET_OUTCOME_POLICY.md"},
                "slippage_policy": {"mode": "tbd", "policy_ref": "MARKET_OUTCOME_POLICY.md §7"},
                "fee_policy": {"mode": "tbd", "policy_ref": "MARKET_OUTCOME_POLICY.md §7"},
                "expiry_policy": {"mode": "tbd"},
                "is_active": True,
                "sort_order": 10,
            },
            {
                "model_key": "first_touch_limit",
                "display_name": "First touch limit",
                "description": "Первое касание зоны входа по свечам (см. MARKET_OUTCOME_POLICY §6).",
                "fill_rule": {"variant": "first_touch_entry_zone", "policy_ref": "MARKET_OUTCOME_POLICY.md"},
                "slippage_policy": {"mode": "tbd"},
                "fee_policy": {"mode": "tbd"},
                "expiry_policy": {"mode": "tbd"},
                "is_active": True,
                "sort_order": 20,
            },
            {
                "model_key": "midpoint_entry",
                "display_name": "Midpoint entry",
                "description": "Вход по середине зоны entry (entry_zone_low / entry_zone_high).",
                "fill_rule": {"variant": "midpoint_of_entry_zone", "policy_ref": "MARKET_OUTCOME_POLICY.md"},
                "slippage_policy": {"mode": "tbd"},
                "fee_policy": {"mode": "tbd"},
                "expiry_policy": {"mode": "tbd"},
                "is_active": True,
                "sort_order": 30,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_execution_models_is_active", table_name="execution_models")
    op.drop_index("ix_execution_models_model_key", table_name="execution_models")
    op.drop_table("execution_models")
