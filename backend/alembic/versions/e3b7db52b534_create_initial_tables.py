"""Create initial tables

Revision ID: e3b7db52b534
Revises: 
Create Date: 2025-07-03 09:20:58.842565

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e3b7db52b534'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('role', sa.Enum('FREE_USER', 'PREMIUM_USER', 'ADMIN', 'CHANNEL_OWNER', name='userrole'), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('login_count', sa.Integer(), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=True),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('email_verification_token', sa.String(length=255), nullable=True),
        sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_reset_token', sa.String(length=255), nullable=True),
        sa.Column('password_reset_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_subscription_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_stripe_customer_id'), 'users', ['stripe_customer_id'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create channels table
    op.create_table('channels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('url', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('signals_count', sa.Integer(), nullable=True),
        sa.Column('successful_signals', sa.Integer(), nullable=True),
        sa.Column('average_roi', sa.Float(), nullable=True),
        sa.Column('max_drawdown', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_channels_category'), 'channels', ['category'], unique=False)
    op.create_index(op.f('ix_channels_id'), 'channels', ['id'], unique=False)
    op.create_index(op.f('ix_channels_name'), 'channels', ['name'], unique=False)
    op.create_index(op.f('ix_channels_platform'), 'channels', ['platform'], unique=False)
    op.create_index(op.f('ix_channels_url'), 'channels', ['url'], unique=True)

    # Create subscriptions table
    op.create_table('subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('plan', sa.Enum('FREE', 'PREMIUM_MONTHLY', 'PREMIUM_YEARLY', name='subscriptionplan'), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'CANCELLED', 'EXPIRED', 'PENDING', 'TRIALING', 'PAST_DUE', name='subscriptionstatus'), nullable=False),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_price_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_product_id', sa.String(length=255), nullable=True),
        sa.Column('api_requests_limit', sa.Integer(), nullable=True),
        sa.Column('can_access_all_channels', sa.Boolean(), nullable=True),
        sa.Column('can_export_data', sa.Boolean(), nullable=True),
        sa.Column('can_use_api', sa.Boolean(), nullable=True),
        sa.Column('max_channels_access', sa.Integer(), nullable=True),
        sa.Column('next_billing_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('auto_renew', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscriptions_id'), 'subscriptions', ['id'], unique=False)
    op.create_index(op.f('ix_subscriptions_stripe_subscription_id'), 'subscriptions', ['stripe_subscription_id'], unique=True)
    op.create_index(op.f('ix_subscriptions_user_id'), 'subscriptions', ['user_id'], unique=False)

    # Create api_keys table
    op.create_table('api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('key_hash', sa.String(length=255), nullable=False),
        sa.Column('key_prefix', sa.String(length=20), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'REVOKED', 'EXPIRED', name='apikeystatus'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('requests_per_day', sa.Integer(), nullable=True),
        sa.Column('requests_per_hour', sa.Integer(), nullable=True),
        sa.Column('requests_today', sa.Integer(), nullable=True),
        sa.Column('requests_this_hour', sa.Integer(), nullable=True),
        sa.Column('total_requests', sa.Integer(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_ip', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('can_read_channels', sa.Boolean(), nullable=True),
        sa.Column('can_read_signals', sa.Boolean(), nullable=True),
        sa.Column('can_read_analytics', sa.Boolean(), nullable=True),
        sa.Column('can_export_data', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_api_keys_id'), 'api_keys', ['id'], unique=False)
    op.create_index(op.f('ix_api_keys_key_hash'), 'api_keys', ['key_hash'], unique=True)
    op.create_index(op.f('ix_api_keys_user_id'), 'api_keys', ['user_id'], unique=False)

    # Create payments table
    op.create_table('payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'SUCCEEDED', 'FAILED', 'CANCELLED', 'REFUNDED', 'PARTIALLY_REFUNDED', name='paymentstatus'), nullable=False),
        sa.Column('payment_method', sa.Enum('STRIPE_CARD', 'STRIPE_BANK', 'STRIPE_WALLET', 'CRYPTO', 'OTHER', name='paymentmethod'), nullable=False),
        sa.Column('stripe_payment_intent_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_invoice_id', sa.String(length=255), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failure_reason', sa.String(length=500), nullable=True),
        sa.Column('failure_code', sa.String(length=50), nullable=True),
        sa.Column('refunded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('refund_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('refund_reason', sa.String(length=500), nullable=True),
        sa.Column('stripe_refund_id', sa.String(length=255), nullable=True),
        sa.Column('payment_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('receipt_url', sa.String(length=500), nullable=True),
        sa.Column('invoice_pdf_url', sa.String(length=500), nullable=True),
        sa.Column('billing_name', sa.String(length=255), nullable=True),
        sa.Column('billing_email', sa.String(length=255), nullable=True),
        sa.Column('billing_address', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('internal_transaction_id', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_id'), 'payments', ['id'], unique=False)
    op.create_index(op.f('ix_payments_internal_transaction_id'), 'payments', ['internal_transaction_id'], unique=True)
    op.create_index(op.f('ix_payments_stripe_payment_intent_id'), 'payments', ['stripe_payment_intent_id'], unique=True)
    op.create_index(op.f('ix_payments_user_id'), 'payments', ['user_id'], unique=False)

    # Create performance_metrics table
    op.create_table('performance_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('channel_id', sa.Integer(), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_type', sa.String(length=20), nullable=False),
        sa.Column('total_signals', sa.Integer(), nullable=True),
        sa.Column('successful_signals', sa.Integer(), nullable=True),
        sa.Column('failed_signals', sa.Integer(), nullable=True),
        sa.Column('pending_signals', sa.Integer(), nullable=True),
        sa.Column('cancelled_signals', sa.Integer(), nullable=True),
        sa.Column('win_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('average_roi', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('total_roi', sa.Numeric(precision=15, scale=4), nullable=True),
        sa.Column('best_signal_roi', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('worst_signal_roi', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('max_drawdown', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('sharpe_ratio', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('volatility', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('risk_reward_ratio', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('consistency_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('profit_factor', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('average_signal_duration', sa.Integer(), nullable=True),
        sa.Column('fastest_success_time', sa.Integer(), nullable=True),
        sa.Column('slowest_success_time', sa.Integer(), nullable=True),
        sa.Column('asset_breakdown', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('direction_breakdown', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('quality_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('rank_in_period', sa.Integer(), nullable=True),
        sa.Column('percentile', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('calculation_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('data_points_used', sa.Integer(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('has_sufficient_data', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['channel_id'], ['channels.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_performance_metrics_channel_id'), 'performance_metrics', ['channel_id'], unique=False)
    op.create_index(op.f('ix_performance_metrics_id'), 'performance_metrics', ['id'], unique=False)
    op.create_index(op.f('ix_performance_metrics_period_end'), 'performance_metrics', ['period_end'], unique=False)
    op.create_index(op.f('ix_performance_metrics_period_start'), 'performance_metrics', ['period_start'], unique=False)
    op.create_index(op.f('ix_performance_metrics_period_type'), 'performance_metrics', ['period_type'], unique=False)

    # Create signals table
    op.create_table('signals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('channel_id', sa.Integer(), nullable=False),
        sa.Column('asset', sa.String(length=20), nullable=False),
        sa.Column('direction', sa.Enum('LONG', 'SHORT', 'BUY', 'SELL', name='signaldirection'), nullable=False),
        sa.Column('entry_price', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('tp1_price', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('tp2_price', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('tp3_price', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('stop_loss', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('entry_price_low', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('entry_price_high', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('original_text', sa.Text(), nullable=True),
        sa.Column('message_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('telegram_message_id', sa.String(length=50), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'ENTRY_HIT', 'TP1_HIT', 'TP2_HIT', 'TP3_HIT', 'SL_HIT', 'EXPIRED', 'CANCELLED', name='signalstatus'), nullable=True),
        sa.Column('entry_hit_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tp1_hit_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tp2_hit_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tp3_hit_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sl_hit_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('final_exit_price', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('final_exit_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('profit_loss_percentage', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('profit_loss_absolute', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancellation_reason', sa.String(length=255), nullable=True),
        sa.Column('is_successful', sa.Boolean(), nullable=True),
        sa.Column('reached_tp1', sa.Boolean(), nullable=True),
        sa.Column('reached_tp2', sa.Boolean(), nullable=True),
        sa.Column('reached_tp3', sa.Boolean(), nullable=True),
        sa.Column('hit_stop_loss', sa.Boolean(), nullable=True),
        sa.Column('ml_success_probability', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('ml_predicted_roi', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('is_ml_prediction_correct', sa.Boolean(), nullable=True),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('risk_reward_ratio', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.ForeignKeyConstraint(['channel_id'], ['channels.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_signals_asset'), 'signals', ['asset'], unique=False)
    op.create_index(op.f('ix_signals_channel_id'), 'signals', ['channel_id'], unique=False)
    op.create_index(op.f('ix_signals_id'), 'signals', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_signals_id'), table_name='signals')
    op.drop_index(op.f('ix_signals_channel_id'), table_name='signals')
    op.drop_index(op.f('ix_signals_asset'), table_name='signals')
    op.drop_table('signals')
    op.drop_index(op.f('ix_performance_metrics_period_type'), table_name='performance_metrics')
    op.drop_index(op.f('ix_performance_metrics_period_start'), table_name='performance_metrics')
    op.drop_index(op.f('ix_performance_metrics_period_end'), table_name='performance_metrics')
    op.drop_index(op.f('ix_performance_metrics_id'), table_name='performance_metrics')
    op.drop_index(op.f('ix_performance_metrics_channel_id'), table_name='performance_metrics')
    op.drop_table('performance_metrics')
    op.drop_index(op.f('ix_payments_user_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_stripe_payment_intent_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_internal_transaction_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_id'), table_name='payments')
    op.drop_table('payments')
    op.drop_index(op.f('ix_api_keys_user_id'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_key_hash'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_id'), table_name='api_keys')
    op.drop_table('api_keys')
    op.drop_index(op.f('ix_subscriptions_user_id'), table_name='subscriptions')
    op.drop_index(op.f('ix_subscriptions_stripe_subscription_id'), table_name='subscriptions')
    op.drop_index(op.f('ix_subscriptions_id'), table_name='subscriptions')
    op.drop_table('subscriptions')
    op.drop_index(op.f('ix_channels_url'), table_name='channels')
    op.drop_index(op.f('ix_channels_platform'), table_name='channels')
    op.drop_index(op.f('ix_channels_name'), table_name='channels')
    op.drop_index(op.f('ix_channels_id'), table_name='channels')
    op.drop_index(op.f('ix_channels_category'), table_name='channels')
    op.drop_table('channels')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_stripe_customer_id'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
