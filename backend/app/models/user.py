from sqlalchemy import Column, String, Boolean, DateTime, Enum, Integer, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from datetime import datetime
from typing import Dict, Any, Optional

from .base import BaseModel

class UserRole(str, enum.Enum):
    FREE_USER = "FREE_USER"
    PREMIUM_USER = "PREMIUM_USER"
    PRO_USER = "PRO_USER"
    ADMIN = "ADMIN"
    CHANNEL_OWNER = "CHANNEL_OWNER"

class SubscriptionPlan(str, enum.Enum):
    FREE = "free"
    PREMIUM = "premium"
    PRO = "pro"

class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PAST_DUE = "past_due"
    TRIALING = "trialing"

class User(BaseModel):
    """
    Model representing a user of the platform
    """
    __tablename__ = "users"
    
    # Basic info
    email = Column(String(255), nullable=False, unique=True, index=True)
    username = Column(String(100), nullable=True, unique=True, index=True)
    full_name = Column(String(255), nullable=True)
    
    # Authentication
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Role and permissions
    role = Column(Enum(UserRole), default=UserRole.FREE_USER)
    
    # Subscription and billing
    subscription_plan = Column(Enum(SubscriptionPlan), default=SubscriptionPlan.FREE)
    subscription_status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    subscription_start_date = Column(DateTime(timezone=True), nullable=True)
    subscription_end_date = Column(DateTime(timezone=True), nullable=True)
    stripe_customer_id = Column(String(255), nullable=True, unique=True)
    stripe_subscription_id = Column(String(255), nullable=True, unique=True)
    
    # Usage limits and tracking
    channels_limit = Column(Integer, default=3)  # Free: 3, Premium: 50, Pro: unlimited
    api_calls_limit = Column(Integer, default=100)  # Free: 100/day, Premium: 1000/day, Pro: unlimited
    api_calls_used_today = Column(Integer, default=0)
    last_api_reset = Column(DateTime(timezone=True), default=func.now())
    
    # Feature flags
    features_enabled = Column(JSON, default=lambda: {
        'export_data': False,
        'email_notifications': False,
        'api_access': False,
        'ml_predictions': False,
        'custom_alerts': False,
        'priority_support': False
    })
    
    # Profile
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="en")
    
    # Account status
    last_login = Column(DateTime(timezone=True), nullable=True)
    login_count = Column(Integer, default=0)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # Email verification
    email_verification_token = Column(String(255), nullable=True)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Password reset
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Subscription relationships
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    channels = relationship("Channel", back_populates="owner", cascade="all, delete-orphan")
    signals = relationship("Signal", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    custom_alerts = relationship("CustomAlert", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    
    @property
    def is_premium(self) -> bool:
        """Check if user has active premium subscription"""
        if self.role == UserRole.ADMIN:
            return True
        return (
            self.subscription_plan in [SubscriptionPlan.PREMIUM, SubscriptionPlan.PRO]
            and self.subscription_status == SubscriptionStatus.ACTIVE
            and (self.subscription_end_date is None or self.subscription_end_date > datetime.utcnow())
        )
    
    @property
    def is_pro(self) -> bool:
        """Check if user has active pro subscription"""
        if self.role == UserRole.ADMIN:
            return True
        return (
            self.subscription_plan == SubscriptionPlan.PRO
            and self.subscription_status == SubscriptionStatus.ACTIVE
            and (self.subscription_end_date is None or self.subscription_end_date > datetime.utcnow())
        )
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == UserRole.ADMIN
    
    def can_add_channel(self) -> bool:
        """Check if user can add more channels"""
        if self.is_admin or self.is_pro:
            return True  # Unlimited for Pro and Admin
        
        current_channels = len(self.channels) if self.channels else 0
        return current_channels < self.channels_limit
    
    def can_make_api_call(self) -> bool:
        """Check if user can make API calls"""
        if self.is_admin or self.is_pro:
            return True  # Unlimited for Pro and Admin
        
        # Reset daily counter if needed
        if self.last_api_reset.date() < datetime.utcnow().date():
            return True  # Will be reset in increment_api_calls
        
        return self.api_calls_used_today < self.api_calls_limit
    
    def increment_api_calls(self) -> None:
        """Increment API call counter"""
        # Reset daily counter if needed
        if self.last_api_reset.date() < datetime.utcnow().date():
            self.api_calls_used_today = 0
            self.last_api_reset = func.now()
        
        self.api_calls_used_today += 1
    
    def has_feature(self, feature: str) -> bool:
        """Check if user has access to specific feature"""
        if self.is_admin:
            return True
        
        if not self.features_enabled:
            return False
        
        return self.features_enabled.get(feature, False)
    
    def update_subscription_plan(self, plan: SubscriptionPlan) -> None:
        """Update user subscription plan and associated limits"""
        self.subscription_plan = plan
        
        # Update limits based on plan
        if plan == SubscriptionPlan.FREE:
            self.channels_limit = 3
            self.api_calls_limit = 100
            self.features_enabled = {
                'export_data': False,
                'email_notifications': False,
                'api_access': False,
                'ml_predictions': False,
                'custom_alerts': False,
                'priority_support': False
            }
        elif plan == SubscriptionPlan.PREMIUM:
            self.channels_limit = 50
            self.api_calls_limit = 1000
            self.features_enabled = {
                'export_data': True,
                'email_notifications': True,
                'api_access': False,
                'ml_predictions': False,
                'custom_alerts': False,
                'priority_support': False
            }
        elif plan == SubscriptionPlan.PRO:
            self.channels_limit = 999999  # Unlimited
            self.api_calls_limit = 999999  # Unlimited
            self.features_enabled = {
                'export_data': True,
                'email_notifications': True,
                'api_access': True,
                'ml_predictions': True,
                'custom_alerts': True,
                'priority_support': True
            }
    
    def __repr__(self):
        return f"<User {self.email} ({self.subscription_plan})>" 