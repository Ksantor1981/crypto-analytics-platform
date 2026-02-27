"""Add feedback, custom_alerts, signal_results, trading tables

Revision ID: a1b2c3d4e5f6
Revises: add_subscription_rbac
Create Date: 2026-02-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'add_subscription_rbac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Feedback table
    op.create_table(
        'feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('user_email', sa.String(length=255), nullable=True),
        sa.Column('user_telegram', sa.String(length=100), nullable=True),
        sa.Column('feedback_type', sa.String(length=30), nullable=False),
        sa.Column('subject', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('admin_response', sa.Text(), nullable=True),
        sa.Column('admin_id', sa.Integer(), nullable=True),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('tags', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feedback_id'), 'feedback', ['id'], unique=False)

    # Custom alerts
    op.create_table(
        'custom_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('condition', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_recurring', sa.Boolean(), nullable=True),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_custom_alerts_id'), 'custom_alerts', ['id'], unique=False)

    # Signal results
    op.create_table(
        'signal_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('signal_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('pnl', sa.Numeric(precision=15, scale=8), nullable=True),
        sa.Column('pnl_percent', sa.Float(), nullable=True),
        sa.Column('entry_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('exit_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('model_version', sa.String(length=50), nullable=True),
        sa.Column('ml_metadata', sa.JSON(), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['signal_id'], ['signals.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('signal_id')
    )
    op.create_index(op.f('ix_signal_results_id'), 'signal_results', ['id'], unique=False)
    op.create_index(op.f('ix_signal_results_signal_id'), 'signal_results', ['signal_id'], unique=True)

    # Trading accounts
    op.create_table(
        'trading_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('exchange', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('api_key_encrypted', sa.Text(), nullable=False),
        sa.Column('api_secret_encrypted', sa.Text(), nullable=False),
        sa.Column('passphrase_encrypted', sa.Text(), nullable=True),
        sa.Column('max_position_size', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('max_daily_loss', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('risk_per_trade', sa.Float(), nullable=True),
        sa.Column('auto_trading_enabled', sa.Boolean(), nullable=True),
        sa.Column('max_open_positions', sa.Integer(), nullable=True),
        sa.Column('min_signal_confidence', sa.Float(), nullable=True),
        sa.Column('total_balance', sa.Numeric(precision=15, scale=8), nullable=True),
        sa.Column('available_balance', sa.Numeric(precision=15, scale=8), nullable=True),
        sa.Column('total_pnl', sa.Numeric(precision=15, scale=8), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trading_accounts_id'), 'trading_accounts', ['id'], unique=False)

    # Risk management
    op.create_table(
        'risk_management',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('max_position_size_usd', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('max_daily_loss_usd', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('max_portfolio_risk', sa.Float(), nullable=True),
        sa.Column('max_correlation', sa.Float(), nullable=True),
        sa.Column('default_stop_loss_percent', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_risk_management_id'), 'risk_management', ['id'], unique=False)

    # Trading positions (depends on trading_accounts)
    op.create_table(
        'trading_positions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('signal_id', sa.Integer(), nullable=True),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('side', sa.String(length=20), nullable=False),
        sa.Column('size', sa.Numeric(precision=15, scale=8), nullable=False),
        sa.Column('entry_price', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('stop_loss', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('take_profit', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('trailing_stop', sa.Boolean(), nullable=True),
        sa.Column('trailing_stop_distance', sa.Float(), nullable=True),
        sa.Column('current_price', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('unrealized_pnl', sa.Numeric(precision=15, scale=8), nullable=True),
        sa.Column('unrealized_pnl_percent', sa.Float(), nullable=True),
        sa.Column('is_open', sa.Boolean(), nullable=True),
        sa.Column('opened_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('exit_price', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('realized_pnl', sa.Numeric(precision=15, scale=8), nullable=True),
        sa.Column('realized_pnl_percent', sa.Float(), nullable=True),
        sa.Column('exchange_order_id', sa.String(length=255), nullable=True),
        sa.Column('exchange_position_id', sa.String(length=255), nullable=True),
        sa.Column('position_metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['trading_accounts.id'], ),
        sa.ForeignKeyConstraint(['signal_id'], ['signals.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trading_positions_id'), 'trading_positions', ['id'], unique=False)

    # Trading orders
    op.create_table(
        'trading_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('position_id', sa.Integer(), nullable=True),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('order_type', sa.String(length=20), nullable=False),
        sa.Column('side', sa.String(length=20), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=15, scale=8), nullable=False),
        sa.Column('price', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('filled_quantity', sa.Numeric(precision=15, scale=8), nullable=True),
        sa.Column('average_fill_price', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('exchange_order_id', sa.String(length=255), nullable=True),
        sa.Column('exchange_client_order_id', sa.String(length=255), nullable=True),
        sa.Column('filled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('order_metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['trading_accounts.id'], ),
        sa.ForeignKeyConstraint(['position_id'], ['trading_positions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trading_orders_id'), 'trading_orders', ['id'], unique=False)
    op.create_index(op.f('ix_trading_orders_exchange_order_id'), 'trading_orders', ['exchange_order_id'], unique=True)

    # Trading strategies
    op.create_table(
        'trading_strategies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('strategy_type', sa.String(length=30), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('total_trades', sa.Integer(), nullable=True),
        sa.Column('winning_trades', sa.Integer(), nullable=True),
        sa.Column('total_pnl', sa.Numeric(precision=15, scale=8), nullable=True),
        sa.Column('win_rate', sa.Float(), nullable=True),
        sa.Column('max_drawdown', sa.Float(), nullable=True),
        sa.Column('sharpe_ratio', sa.Float(), nullable=True),
        sa.Column('last_executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['trading_accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trading_strategies_id'), 'trading_strategies', ['id'], unique=False)


def downgrade() -> None:
    op.drop_table('trading_strategies')
    op.drop_index(op.f('ix_trading_orders_exchange_order_id'), table_name='trading_orders')
    op.drop_table('trading_orders')
    op.drop_table('trading_positions')
    op.drop_table('risk_management')
    op.drop_table('trading_accounts')
    op.drop_index(op.f('ix_signal_results_signal_id'), table_name='signal_results')
    op.drop_index(op.f('ix_signal_results_id'), table_name='signal_results')
    op.drop_table('signal_results')
    op.drop_index(op.f('ix_custom_alerts_id'), table_name='custom_alerts')
    op.drop_table('custom_alerts')
    op.drop_index(op.f('ix_feedback_id'), table_name='feedback')
    op.drop_table('feedback')
