"""Add subscription and RBAC fields to users

Revision ID: add_subscription_rbac
Revises: previous_revision
Create Date: 2025-01-23 20:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_subscription_rbac'
down_revision = 'previous_revision'  # Update this with actual previous revision
branch_labels = None
depends_on = None

def upgrade():
    # Add new enum types
    subscription_plan_enum = postgresql.ENUM('free', 'premium', 'pro', name='subscriptionplan')
    subscription_plan_enum.create(op.get_bind())
    
    subscription_status_enum = postgresql.ENUM('active', 'cancelled', 'expired', 'past_due', 'trialing', name='subscriptionstatus')
    subscription_status_enum.create(op.get_bind())
    
    # Add new columns to users table
    op.add_column('users', sa.Column('subscription_plan', subscription_plan_enum, nullable=False, server_default='free'))
    op.add_column('users', sa.Column('subscription_status', subscription_status_enum, nullable=False, server_default='active'))
    op.add_column('users', sa.Column('subscription_start_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('subscription_end_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('stripe_customer_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('stripe_subscription_id', sa.String(255), nullable=True))
    
    # Usage limits and tracking
    op.add_column('users', sa.Column('channels_limit', sa.Integer(), nullable=False, server_default='3'))
    op.add_column('users', sa.Column('api_calls_limit', sa.Integer(), nullable=False, server_default='100'))
    op.add_column('users', sa.Column('api_calls_used_today', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('last_api_reset', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    
    # Feature flags as JSON
    op.add_column('users', sa.Column('features_enabled', sa.JSON(), nullable=True, server_default=sa.text("'{\"export_data\": false, \"email_notifications\": false, \"api_access\": false, \"ml_predictions\": false, \"custom_alerts\": false, \"priority_support\": false}'")))
    
    # Add unique constraints
    op.create_unique_constraint('uq_users_stripe_customer_id', 'users', ['stripe_customer_id'])
    op.create_unique_constraint('uq_users_stripe_subscription_id', 'users', ['stripe_subscription_id'])
    
    # Update existing users to have default feature flags
    op.execute("""
        UPDATE users 
        SET features_enabled = '{"export_data": false, "email_notifications": false, "api_access": false, "ml_predictions": false, "custom_alerts": false, "priority_support": false}'
        WHERE features_enabled IS NULL
    """)

def downgrade():
    # Remove constraints
    op.drop_constraint('uq_users_stripe_subscription_id', 'users', type_='unique')
    op.drop_constraint('uq_users_stripe_customer_id', 'users', type_='unique')
    
    # Remove columns
    op.drop_column('users', 'features_enabled')
    op.drop_column('users', 'last_api_reset')
    op.drop_column('users', 'api_calls_used_today')
    op.drop_column('users', 'api_calls_limit')
    op.drop_column('users', 'channels_limit')
    op.drop_column('users', 'stripe_subscription_id')
    op.drop_column('users', 'stripe_customer_id')
    op.drop_column('users', 'subscription_end_date')
    op.drop_column('users', 'subscription_start_date')
    op.drop_column('users', 'subscription_status')
    op.drop_column('users', 'subscription_plan')
    
    # Drop enum types
    subscription_status_enum = postgresql.ENUM('active', 'cancelled', 'expired', 'past_due', 'trialing', name='subscriptionstatus')
    subscription_status_enum.drop(op.get_bind())
    
    subscription_plan_enum = postgresql.ENUM('free', 'premium', 'pro', name='subscriptionplan')
    subscription_plan_enum.drop(op.get_bind())
