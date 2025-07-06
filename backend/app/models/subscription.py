from sqlalchemy import Column, String, Boolean, DateTime, Enum, Integer, ForeignKey, Numeric
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from decimal import Decimal

from .base import BaseModel

class SubscriptionPlan(str, enum.Enum):
    FREE = "FREE"
    PREMIUM_MONTHLY = "PREMIUM_MONTHLY"
    PREMIUM_YEARLY = "PREMIUM_YEARLY"

class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    PENDING = "PENDING"
    TRIALING = "TRIALING"
    PAST_DUE = "PAST_DUE"

class Subscription(BaseModel):
    """
    Model representing user subscriptions
    """
    __tablename__ = "subscriptions"
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="subscriptions")
    
    # Subscription details
    plan = Column(Enum(SubscriptionPlan), nullable=False)
    status = Column(Enum(SubscriptionStatus), nullable=False)
    
    # Pricing
    price = Column(Numeric(10, 2), nullable=False)  # Monthly price
    currency = Column(String(3), default="USD")
    
    # Dates
    started_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    ends_at = Column(DateTime(timezone=True), nullable=True)
    trial_start = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    
    # Stripe integration
    stripe_subscription_id = Column(String(255), nullable=True, unique=True)
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_price_id = Column(String(255), nullable=True)
    stripe_product_id = Column(String(255), nullable=True)
    
    # Features and limits
    api_requests_limit = Column(Integer, nullable=True)  # per day
    can_access_all_channels = Column(Boolean, default=False)
    can_export_data = Column(Boolean, default=False)
    can_use_api = Column(Boolean, default=False)
    max_channels_access = Column(Integer, default=5)  # for free users
    
    # Billing
    next_billing_date = Column(DateTime(timezone=True), nullable=True)
    auto_renew = Column(Boolean, default=True)
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is currently active"""
        now = datetime.utcnow()
        return (
            self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]
            and self.current_period_end > now
        )
    
    @property
    def is_trial(self) -> bool:
        """Check if subscription is in trial period"""
        if not self.trial_start or not self.trial_end:
            return False
        now = datetime.utcnow()
        return self.trial_start <= now <= self.trial_end
    
    @property
    def days_until_expiry(self) -> int:
        """Get days until subscription expires"""
        if not self.current_period_end:
            return 0
        delta = self.current_period_end - datetime.utcnow()
        return max(0, delta.days)
    
    def __repr__(self):
        return f"<Subscription {self.plan} - {self.status}>" 