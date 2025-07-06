from sqlalchemy import Column, String, Boolean, DateTime, Enum, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
import enum
from datetime import datetime, timedelta
import secrets

from .base import BaseModel

class APIKeyStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"

class APIKey(BaseModel):
    """
    Model representing API keys for users
    """
    __tablename__ = "api_keys"
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="api_keys")
    
    # Key details
    name = Column(String(255), nullable=False)  # User-friendly name
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    key_prefix = Column(String(20), nullable=False)  # First few characters for identification
    
    # Status and permissions
    status = Column(Enum(APIKeyStatus), default=APIKeyStatus.ACTIVE)
    is_active = Column(Boolean, default=True)
    
    # Usage limits
    requests_per_day = Column(Integer, default=1000)
    requests_per_hour = Column(Integer, default=100)
    requests_today = Column(Integer, default=0)
    requests_this_hour = Column(Integer, default=0)
    total_requests = Column(Integer, default=0)
    
    # Timestamps
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Tracking
    last_ip = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    
    # Permissions (JSON field would be better, but keeping simple for now)
    can_read_channels = Column(Boolean, default=True)
    can_read_signals = Column(Boolean, default=True)
    can_read_analytics = Column(Boolean, default=False)  # Premium feature
    can_export_data = Column(Boolean, default=False)  # Premium feature
    
    @staticmethod
    def generate_key() -> tuple[str, str]:
        """Generate a new API key and its hash"""
        # Generate secure random key
        key = f"cap_{secrets.token_urlsafe(32)}"
        # Create hash for storage (in real app, use proper hashing)
        key_hash = f"hash_{secrets.token_urlsafe(32)}"
        return key, key_hash
    
    @property
    def is_expired(self) -> bool:
        """Check if API key is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_rate_limited(self) -> bool:
        """Check if API key has exceeded rate limits"""
        if self.requests_today >= self.requests_per_day:
            return True
        if self.requests_this_hour >= self.requests_per_hour:
            return True
        return False
    
    def can_make_request(self) -> bool:
        """Check if API key can make a request"""
        return (
            self.is_active 
            and self.status == APIKeyStatus.ACTIVE 
            and not self.is_expired 
            and not self.is_rate_limited
        )
    
    def increment_usage(self, ip: str = None, user_agent: str = None):
        """Increment usage counters"""
        self.total_requests += 1
        self.requests_today += 1
        self.requests_this_hour += 1
        self.last_used_at = datetime.utcnow()
        
        if ip:
            self.last_ip = ip
        if user_agent:
            self.user_agent = user_agent
    
    def __repr__(self):
        return f"<APIKey {self.name} - {self.key_prefix}***>" 