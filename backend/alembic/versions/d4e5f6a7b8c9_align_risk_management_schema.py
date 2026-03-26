"""Align risk_management table with ORM model.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-03-26 17:38:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("ALTER TABLE risk_management ADD COLUMN IF NOT EXISTS trailing_stop_enabled BOOLEAN"))
    op.execute(sa.text("ALTER TABLE risk_management ADD COLUMN IF NOT EXISTS trailing_stop_distance DOUBLE PRECISION"))
    op.execute(sa.text("ALTER TABLE risk_management ADD COLUMN IF NOT EXISTS risk_per_trade DOUBLE PRECISION"))
    op.execute(sa.text("ALTER TABLE risk_management ADD COLUMN IF NOT EXISTS max_positions_per_symbol INTEGER"))
    op.execute(sa.text("ALTER TABLE risk_management ADD COLUMN IF NOT EXISTS max_total_positions INTEGER"))
    op.execute(sa.text("ALTER TABLE risk_management ADD COLUMN IF NOT EXISTS trading_hours_start VARCHAR(5)"))
    op.execute(sa.text("ALTER TABLE risk_management ADD COLUMN IF NOT EXISTS trading_hours_end VARCHAR(5)"))
    op.execute(sa.text("ALTER TABLE risk_management ADD COLUMN IF NOT EXISTS weekend_trading BOOLEAN"))
    op.execute(sa.text("ALTER TABLE risk_management ADD COLUMN IF NOT EXISTS min_volume_usd NUMERIC(15,2)"))
    op.execute(sa.text("ALTER TABLE risk_management ADD COLUMN IF NOT EXISTS max_spread_percent DOUBLE PRECISION"))

    op.execute(sa.text("UPDATE risk_management SET trailing_stop_enabled = true WHERE trailing_stop_enabled IS NULL"))
    op.execute(sa.text("UPDATE risk_management SET trailing_stop_distance = 0.01 WHERE trailing_stop_distance IS NULL"))
    op.execute(sa.text("UPDATE risk_management SET risk_per_trade = 0.02 WHERE risk_per_trade IS NULL"))
    op.execute(sa.text("UPDATE risk_management SET max_positions_per_symbol = 1 WHERE max_positions_per_symbol IS NULL"))
    op.execute(sa.text("UPDATE risk_management SET max_total_positions = 5 WHERE max_total_positions IS NULL"))
    op.execute(sa.text("UPDATE risk_management SET trading_hours_start = '00:00' WHERE trading_hours_start IS NULL"))
    op.execute(sa.text("UPDATE risk_management SET trading_hours_end = '23:59' WHERE trading_hours_end IS NULL"))
    op.execute(sa.text("UPDATE risk_management SET weekend_trading = false WHERE weekend_trading IS NULL"))
    op.execute(sa.text("UPDATE risk_management SET min_volume_usd = 1000000.00 WHERE min_volume_usd IS NULL"))
    op.execute(sa.text("UPDATE risk_management SET max_spread_percent = 0.005 WHERE max_spread_percent IS NULL"))


def downgrade() -> None:
    op.execute(sa.text("ALTER TABLE risk_management DROP COLUMN IF EXISTS max_spread_percent"))
    op.execute(sa.text("ALTER TABLE risk_management DROP COLUMN IF EXISTS min_volume_usd"))
    op.execute(sa.text("ALTER TABLE risk_management DROP COLUMN IF EXISTS weekend_trading"))
    op.execute(sa.text("ALTER TABLE risk_management DROP COLUMN IF EXISTS trading_hours_end"))
    op.execute(sa.text("ALTER TABLE risk_management DROP COLUMN IF EXISTS trading_hours_start"))
    op.execute(sa.text("ALTER TABLE risk_management DROP COLUMN IF EXISTS max_total_positions"))
    op.execute(sa.text("ALTER TABLE risk_management DROP COLUMN IF EXISTS max_positions_per_symbol"))
    op.execute(sa.text("ALTER TABLE risk_management DROP COLUMN IF EXISTS risk_per_trade"))
    op.execute(sa.text("ALTER TABLE risk_management DROP COLUMN IF EXISTS trailing_stop_distance"))
    op.execute(sa.text("ALTER TABLE risk_management DROP COLUMN IF EXISTS trailing_stop_enabled"))
