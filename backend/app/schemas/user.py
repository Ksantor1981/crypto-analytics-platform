from typing import Optional, List, ForwardRef
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from enum import Enum

# Forward references for circular dependencies
Subscription = ForwardRef('Subscription')

class UserRole(str, Enum):
    FREE_USER = "FREE_USER"
    PREMIUM_USER = "PREMIUM_USER"
    ADMIN = "ADMIN"
    CHANNEL_OWNER = "CHANNEL_OWNER"


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.FREE_USER
    is_active: bool = True


class UserCreate(UserBase):
    password: str
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class UserChangePassword(BaseModel):
    current_password: str
    new_password: str
    confirm_new_password: str
    
    @validator('confirm_new_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('New passwords do not match')
        return v
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v


class UserInDB(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    subscriptions: List['Subscription'] = []
    
    class Config:
        from_attributes = True


class UserResponse(UserInDB):
    """User response model without sensitive data."""
    pass


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes


class TokenRefresh(BaseModel):
    refresh_token: str


class UserProfile(BaseModel):
    """Extended user profile with subscription details."""
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
    subscription: Optional['Subscription'] = None
    
    # Subscription details
    current_subscription_expires: Optional[datetime] = None
    stripe_customer_id: Optional[str] = None
    is_premium: bool = False
    is_admin: bool = False
    
    class Config:
        from_attributes = True


class UserStats(BaseModel):
    """User statistics and usage."""
    total_signals_received: int = 0
    successful_signals: int = 0
    failed_signals: int = 0
    total_profit_loss: float = 0.0
    win_rate: float = 0.0
    active_subscriptions: int = 0
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Response for user list with pagination."""
    users: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
    confirm_new_password: str
    
    @validator('confirm_new_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v 