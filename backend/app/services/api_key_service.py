"""
API Key Management Service - Pro feature
Part of Task 2.3.2: Pro функции
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import secrets
import hashlib

from ..models.user import User, SubscriptionPlan
from ..models.api_key import APIKey, APIKeyStatus
from ..middleware.rbac_middleware import check_subscription_limit

logger = logging.getLogger(__name__)

class APIKeyService:
    """
    Service for managing API keys for Pro users
    Pro feature: Personal API keys with custom permissions
    """
    
    def __init__(self):
        self.max_keys_per_user = {
            SubscriptionPlan.FREE: 0,  # No API access
            SubscriptionPlan.PREMIUM: 0,  # No API access
            SubscriptionPlan.PRO: 5  # Up to 5 API keys
        }
    
    async def create_api_key(
        self,
        user: User,
        db: Session,
        name: str,
        permissions: Optional[Dict[str, bool]] = None,
        expires_in_days: Optional[int] = None,
        rate_limits: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """
        Create a new API key for Pro user
        
        Args:
            user: User requesting API key
            db: Database session
            name: User-friendly name for the key
            permissions: Custom permissions for the key
            expires_in_days: Expiration in days (default: 365)
            rate_limits: Custom rate limits
        
        Returns:
            Dict with API key details (key is only shown once)
        """
        # Check if user has Pro subscription
        await check_subscription_limit(user, feature='api_access', api_call=False)
        
        if user.subscription_plan != SubscriptionPlan.PRO:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API access is only available for Pro subscribers"
            )
        
        # Check if user has reached key limit
        existing_keys = db.query(APIKey).filter(
            APIKey.user_id == user.id,
            APIKey.status == APIKeyStatus.ACTIVE
        ).count()
        
        max_keys = self.max_keys_per_user.get(user.subscription_plan, 0)
        if existing_keys >= max_keys:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum number of API keys ({max_keys}) reached"
            )
        
        # Generate API key
        api_key, key_hash = self._generate_secure_key()
        key_prefix = api_key[:12] + "..."
        
        # Set default permissions for Pro users
        default_permissions = {
            'can_read_channels': True,
            'can_read_signals': True,
            'can_read_analytics': True,
            'can_export_data': True
        }
        
        if permissions:
            default_permissions.update(permissions)
        
        # Set default rate limits for Pro users
        default_rate_limits = {
            'requests_per_day': 10000,
            'requests_per_hour': 1000
        }
        
        if rate_limits:
            default_rate_limits.update(rate_limits)
        
        # Set expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        else:
            expires_at = datetime.utcnow() + timedelta(days=365)  # Default 1 year
        
        # Create API key record
        api_key_record = APIKey(
            user_id=user.id,
            name=name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            status=APIKeyStatus.ACTIVE,
            expires_at=expires_at,
            **default_permissions,
            **default_rate_limits
        )
        
        db.add(api_key_record)
        db.commit()
        db.refresh(api_key_record)
        
        logger.info(f"API key created for user {user.email}: {name}")
        
        return {
            'id': api_key_record.id,
            'name': name,
            'key': api_key,  # Only shown once!
            'key_prefix': key_prefix,
            'permissions': default_permissions,
            'rate_limits': default_rate_limits,
            'expires_at': expires_at.isoformat(),
            'created_at': api_key_record.created_at.isoformat(),
            'warning': 'Save this key securely - it will not be shown again!'
        }
    
    async def list_api_keys(self, user: User, db: Session) -> List[Dict[str, Any]]:
        """List all API keys for user"""
        await check_subscription_limit(user, feature='api_access', api_call=False)
        
        keys = db.query(APIKey).filter(APIKey.user_id == user.id).all()
        
        return [
            {
                'id': key.id,
                'name': key.name,
                'key_prefix': key.key_prefix,
                'status': key.status.value,
                'is_active': key.is_active,
                'is_expired': key.is_expired,
                'permissions': {
                    'can_read_channels': key.can_read_channels,
                    'can_read_signals': key.can_read_signals,
                    'can_read_analytics': key.can_read_analytics,
                    'can_export_data': key.can_export_data
                },
                'rate_limits': {
                    'requests_per_day': key.requests_per_day,
                    'requests_per_hour': key.requests_per_hour
                },
                'usage': {
                    'total_requests': key.total_requests,
                    'requests_today': key.requests_today,
                    'requests_this_hour': key.requests_this_hour
                },
                'last_used_at': key.last_used_at.isoformat() if key.last_used_at else None,
                'expires_at': key.expires_at.isoformat() if key.expires_at else None,
                'created_at': key.created_at.isoformat()
            }
            for key in keys
        ]
    
    async def revoke_api_key(self, user: User, db: Session, key_id: int) -> bool:
        """Revoke an API key"""
        await check_subscription_limit(user, feature='api_access', api_call=False)
        
        api_key = db.query(APIKey).filter(
            APIKey.id == key_id,
            APIKey.user_id == user.id
        ).first()
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        api_key.status = APIKeyStatus.REVOKED
        api_key.is_active = False
        db.commit()
        
        logger.info(f"API key revoked: {api_key.name} for user {user.email}")
        return True
    
    async def update_api_key(
        self,
        user: User,
        db: Session,
        key_id: int,
        name: Optional[str] = None,
        permissions: Optional[Dict[str, bool]] = None,
        rate_limits: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """Update API key settings"""
        await check_subscription_limit(user, feature='api_access', api_call=False)
        
        api_key = db.query(APIKey).filter(
            APIKey.id == key_id,
            APIKey.user_id == user.id
        ).first()
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        # Update fields
        if name:
            api_key.name = name
        
        if permissions:
            for perm, value in permissions.items():
                if hasattr(api_key, perm):
                    setattr(api_key, perm, value)
        
        if rate_limits:
            for limit, value in rate_limits.items():
                if hasattr(api_key, limit):
                    setattr(api_key, limit, value)
        
        db.commit()
        db.refresh(api_key)
        
        logger.info(f"API key updated: {api_key.name} for user {user.email}")
        
        return {
            'id': api_key.id,
            'name': api_key.name,
            'key_prefix': api_key.key_prefix,
            'status': api_key.status.value,
            'updated_at': datetime.utcnow().isoformat()
        }
    
    async def validate_api_key(self, db: Session, api_key: str) -> Optional[APIKey]:
        """
        Validate API key and return APIKey object if valid
        Used by API authentication middleware
        """
        try:
            # Hash the provided key to match stored hash
            key_hash = self._hash_key(api_key)
            
            # Find API key in database
            api_key_record = db.query(APIKey).filter(
                APIKey.key_hash == key_hash
            ).first()
            
            if not api_key_record:
                return None
            
            # Check if key can make request
            if not api_key_record.can_make_request():
                return None
            
            return api_key_record
            
        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return None
    
    async def record_api_usage(
        self,
        db: Session,
        api_key: APIKey,
        endpoint: str,
        ip: str = None,
        user_agent: str = None
    ):
        """Record API usage for analytics and rate limiting"""
        try:
            # Increment usage counters
            api_key.increment_usage(ip=ip, user_agent=user_agent)
            
            # TODO: Record detailed usage analytics
            # api_usage = APIUsage(
            #     api_key_id=api_key.id,
            #     endpoint=endpoint,
            #     ip_address=ip,
            #     user_agent=user_agent,
            #     timestamp=datetime.utcnow()
            # )
            # db.add(api_usage)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error recording API usage: {e}")
    
    def _generate_secure_key(self) -> tuple[str, str]:
        """Generate secure API key and its hash"""
        # Generate secure random key
        random_part = secrets.token_urlsafe(32)
        api_key = f"cap_{random_part}"
        
        # Create hash for storage
        key_hash = self._hash_key(api_key)
        
        return api_key, key_hash
    
    def _hash_key(self, api_key: str) -> str:
        """Hash API key for secure storage"""
        # In production, use proper password hashing like bcrypt
        # For now, using SHA256 with salt
        salt = "crypto_analytics_platform_salt"
        return hashlib.sha256(f"{api_key}{salt}".encode()).hexdigest()
    
    async def get_api_usage_stats(self, user: User, db: Session) -> Dict[str, Any]:
        """Get API usage statistics for user"""
        await check_subscription_limit(user, feature='api_access', api_call=False)
        
        keys = db.query(APIKey).filter(APIKey.user_id == user.id).all()
        
        total_requests = sum(key.total_requests for key in keys)
        requests_today = sum(key.requests_today for key in keys)
        active_keys = len([key for key in keys if key.status == APIKeyStatus.ACTIVE])
        
        return {
            'total_api_keys': len(keys),
            'active_api_keys': active_keys,
            'total_requests': total_requests,
            'requests_today': requests_today,
            'rate_limit_status': {
                key.name: {
                    'requests_today': key.requests_today,
                    'limit_per_day': key.requests_per_day,
                    'usage_percentage': round((key.requests_today / key.requests_per_day) * 100, 2)
                }
                for key in keys if key.status == APIKeyStatus.ACTIVE
            }
        }


# Global API key service instance
api_key_service = APIKeyService()
