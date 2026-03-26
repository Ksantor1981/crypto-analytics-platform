"""Add market data tables for real candles and technical indicators

Revision ID: f4a5b6c7d8e9
Revises: e3b7db52b534
Create Date: 2026-03-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4a5b6c7d8e9'
down_revision: Union[str, None] = 'e3b7db52b534'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create market_candles table for OHLCV data
    op.create_table('market_candles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('timeframe', sa.String(length=10), nullable=False),  # '1m', '5m', '1h', '1d', etc.
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('open', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('high', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('low', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('close', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('volume', sa.Numeric(precision=30, scale=8), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=True),  # 'binance', 'kraken', etc.
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol', 'timeframe', 'timestamp', name='uq_market_candles_symbol_timeframe_timestamp')
    )
    op.create_index(op.f('ix_market_candles_symbol'), 'market_candles', ['symbol'], unique=False)
    op.create_index(op.f('ix_market_candles_timestamp'), 'market_candles', ['timestamp'], unique=False)
    op.create_index(op.f('ix_market_candles_symbol_timestamp'), 'market_candles', ['symbol', 'timestamp'], unique=False)

    # Create technical_indicators table
    op.create_table('technical_indicators',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('timeframe', sa.String(length=10), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('rsi_14', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('rsi_period', sa.Integer(), nullable=True, server_default='14'),
        sa.Column('macd_line', sa.Numeric(precision=15, scale=8), nullable=True),
        sa.Column('macd_signal', sa.Numeric(precision=15, scale=8), nullable=True),
        sa.Column('macd_histogram', sa.Numeric(precision=15, scale=8), nullable=True),
        sa.Column('bb_upper', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('bb_middle', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('bb_lower', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('bb_bandwidth', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('atr_14', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('stoch_k', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('stoch_d', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('adx', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol', 'timeframe', 'timestamp', name='uq_technical_indicators_symbol_timeframe_timestamp')
    )
    op.create_index(op.f('ix_technical_indicators_symbol'), 'technical_indicators', ['symbol'], unique=False)
    op.create_index(op.f('ix_technical_indicators_timestamp'), 'technical_indicators', ['timestamp'], unique=False)

    # Create real_signals table for verified trading signals
    op.create_table('real_signals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('entry_price', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('entry_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('tp1_price', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('tp1_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('stop_loss', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('sl_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('direction', sa.String(length=10), nullable=False),  # 'LONG' or 'SHORT'
        sa.Column('outcome', sa.String(length=20), nullable=True),  # 'TP_HIT', 'SL_HIT', 'EXPIRED', 'CANCELLED'
        sa.Column('outcome_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('roi_percent', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=True),  # 'telegram_channel_name', 'strategy_backtest', etc.
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('risk_reward_ratio', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('verified_by', sa.Integer(), nullable=True),  # user_id
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['verified_by'], ['users.id'], )
    )
    op.create_index(op.f('ix_real_signals_symbol'), 'real_signals', ['symbol'], unique=False)
    op.create_index(op.f('ix_real_signals_entry_date'), 'real_signals', ['entry_date'], unique=False)
    op.create_index(op.f('ix_real_signals_outcome'), 'real_signals', ['outcome'], unique=False)

    # Create signal_backtest_results table for validation
    op.create_table('signal_backtest_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('strategy_name', sa.String(length=255), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_signals', sa.Integer(), nullable=False),
        sa.Column('winning_signals', sa.Integer(), nullable=False),
        sa.Column('losing_signals', sa.Integer(), nullable=False),
        sa.Column('win_rate_percent', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('total_return_percent', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('sharpe_ratio', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('max_drawdown_percent', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('avg_rr_ratio', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_signal_backtest_results_strategy'), 'signal_backtest_results', ['strategy_name'], unique=False)
    op.create_index(op.f('ix_signal_backtest_results_period'), 'signal_backtest_results', ['period_start', 'period_end'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_signal_backtest_results_period'), table_name='signal_backtest_results')
    op.drop_index(op.f('ix_signal_backtest_results_strategy'), table_name='signal_backtest_results')
    op.drop_table('signal_backtest_results')

    op.drop_index(op.f('ix_real_signals_outcome'), table_name='real_signals')
    op.drop_index(op.f('ix_real_signals_entry_date'), table_name='real_signals')
    op.drop_index(op.f('ix_real_signals_symbol'), table_name='real_signals')
    op.drop_table('real_signals')

    op.drop_index(op.f('ix_technical_indicators_timestamp'), table_name='technical_indicators')
    op.drop_index(op.f('ix_technical_indicators_symbol'), table_name='technical_indicators')
    op.drop_table('technical_indicators')

    op.drop_index(op.f('ix_market_candles_symbol_timestamp'), table_name='market_candles')
    op.drop_index(op.f('ix_market_candles_timestamp'), table_name='market_candles')
    op.drop_index(op.f('ix_market_candles_symbol'), table_name='market_candles')
    op.drop_table('market_candles')
