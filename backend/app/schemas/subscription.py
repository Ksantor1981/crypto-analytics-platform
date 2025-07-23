from pydantic import BaseModel, Field, validator, ForwardRef
from typing import Optional, List
from datetime import datetime
from enum import Enum
from decimal import Decimal

# Forward reference for circular dependency
User = ForwardRef('User')

# Enums matching the model
class SubscriptionPlan(str, Enum):
    FREE = "FREE"
    PREMIUM_MONTHLY = "PREMIUM_MONTHLY"
    PREMIUM_YEARLY = "PREMIUM_YEARLY"

class SubscriptionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    PENDING = "PENDING"
    TRIALING = "TRIALING"
    PAST_DUE = "PAST_DUE"

# Base schema for common fields
class SubscriptionBase(BaseModel):
    plan: SubscriptionPlan
    price: float = Field(..., description="Monthly price", gt=0)
    currency: str = Field(default="USD", description="Currency code")
    
    # Features and limits
    api_requests_limit: Optional[int] = Field(None, description="Daily API requests limit")
    can_access_all_channels: bool = Field(default=False, description="Access to all channels")
    can_export_data: bool = Field(default=False, description="Data export capability")
    can_use_api: bool = Field(default=False, description="API access")
    max_channels_access: int = Field(default=5, description="Maximum channels accessible")
    auto_renew: bool = Field(default=True, description="Auto-renewal setting")

# Schema for creating subscription
class SubscriptionCreate(SubscriptionBase):
    user_id: int = Field(..., description="User ID")
    current_period_start: datetime = Field(..., description="Period start date")
    current_period_end: datetime = Field(..., description="Period end date")
    trial_start: Optional[datetime] = Field(None, description="Trial start date")
    trial_end: Optional[datetime] = Field(None, description="Trial end date")
    stripe_price_id: Optional[str] = Field(None, description="Stripe price ID")

# Schema for updating subscription
class SubscriptionUpdate(BaseModel):
    plan: Optional[SubscriptionPlan] = Field(None, description="Subscription plan")
    status: Optional[SubscriptionStatus] = Field(None, description="Subscription status")
    current_period_end: Optional[datetime] = Field(None, description="Period end date")
    cancelled_at: Optional[datetime] = Field(None, description="Cancellation date")
    ends_at: Optional[datetime] = Field(None, description="End date")
    auto_renew: Optional[bool] = Field(None, description="Auto-renewal setting")
    
    # Feature updates
    api_requests_limit: Optional[int] = Field(None, description="Daily API requests limit")
    can_access_all_channels: Optional[bool] = Field(None, description="Access to all channels")
    can_export_data: Optional[bool] = Field(None, description="Data export capability")
    can_use_api: Optional[bool] = Field(None, description="API access")
    max_channels_access: Optional[int] = Field(None, description="Maximum channels accessible")

# Schema for subscription response
class SubscriptionResponse(SubscriptionBase):
    id: int
    user: "User"
    status: SubscriptionStatus
    
    # Dates
    started_at: datetime
    current_period_start: datetime
    current_period_end: datetime
    cancelled_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    next_billing_date: Optional[datetime] = None
    
    # Stripe integration
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    stripe_price_id: Optional[str] = None
    stripe_product_id: Optional[str] = None
    
    # Computed properties
    is_active: bool = False
    is_trial: bool = False
    days_until_expiry: int = 0
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Schema with user info
class SubscriptionWithUser(SubscriptionResponse):
    user_email: Optional[str] = None
    user_name: Optional[str] = None

# Schema for subscription plans catalog
class SubscriptionPlanInfo(BaseModel):
    plan: SubscriptionPlan
    name: str
    description: str
    price_monthly: float
    price_yearly: Optional[float] = None
    currency: str = "USD"
    features: List[str]
    api_requests_limit: Optional[int] = None
    max_channels_access: int = 5
    can_access_all_channels: bool = False
    can_export_data: bool = False
    can_use_api: bool = False
    stripe_price_id_monthly: Optional[str] = None
    stripe_price_id_yearly: Optional[str] = None
    is_popular: bool = False

# Schema for subscription statistics
class SubscriptionStats(BaseModel):
    total_subscriptions: int = 0
    active_subscriptions: int = 0
    trial_subscriptions: int = 0
    cancelled_subscriptions: int = 0
    expired_subscriptions: int = 0
    
    # Revenue stats
    monthly_revenue: float = 0.0
    yearly_revenue: float = 0.0
    total_revenue: float = 0.0
    
    # Plan breakdown
    free_users: int = 0
    premium_monthly_users: int = 0
    premium_yearly_users: int = 0
    
    # Conversion metrics
    trial_conversion_rate: float = 0.0
    churn_rate: float = 0.0

# Schema for subscription usage
class SubscriptionUsage(BaseModel):
    subscription_id: int
    api_requests_used: int = 0
    api_requests_limit: Optional[int] = None
    channels_accessed: int = 0
    max_channels_access: int = 5
    data_exports_used: int = 0
    period_start: datetime
    period_end: datetime
    
    @property
    def api_usage_percentage(self) -> float:
        if not self.api_requests_limit:
            return 0.0
        return min(100.0, (self.api_requests_used / self.api_requests_limit) * 100)
    
    @property
    def channels_usage_percentage(self) -> float:
        if self.max_channels_access == 0:
            return 100.0
        return min(100.0, (self.channels_accessed / self.max_channels_access) * 100)

# Schema for paginated subscription list
class SubscriptionListResponse(BaseModel):
    subscriptions: List[SubscriptionWithUser]
    total: int
    page: int
    size: int
    pages: int

# Schema for subscription cancellation
class SubscriptionCancellation(BaseModel):
    reason: Optional[str] = Field(None, description="Cancellation reason")
    immediate: bool = Field(default=False, description="Cancel immediately or at period end")
    feedback: Optional[str] = Field(None, description="User feedback")

# Schema for subscription renewal
class SubscriptionRenewal(BaseModel):
    plan: Optional[SubscriptionPlan] = Field(None, description="New plan for renewal")
    auto_renew: bool = Field(default=True, description="Enable auto-renewal")

# Schema for Stripe webhook data
class StripeWebhookData(BaseModel):
    event_type: str
    subscription_id: str
    customer_id: str
    status: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None 