from sqlalchemy import Column, String, Boolean, DateTime, Enum, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from datetime import datetime

from .base import BaseModel

class UserRole(str, enum.Enum):
    FREE_USER = "FREE_USER"
    PREMIUM_USER = "PREMIUM_USER"
    ADMIN = "ADMIN"
    CHANNEL_OWNER = "CHANNEL_OWNER"

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
    
    # Subscription info (will be linked to Subscription model)
    current_subscription_expires = Column(DateTime(timezone=True), nullable=True)
    stripe_customer_id = Column(String(255), nullable=True, unique=True)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    
    @property
    def is_premium(self) -> bool:
        """Check if user has active premium subscription"""
        if self.role == UserRole.ADMIN:
            return True
        return (
            self.current_subscription_expires is not None 
            and self.current_subscription_expires > datetime.utcnow()
        )
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == UserRole.ADMIN
    
    def __repr__(self):
        return f"<User {self.email} ({self.role})>" 