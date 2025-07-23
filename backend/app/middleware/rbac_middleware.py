"""
RBAC Middleware - Role-Based Access Control and Subscription Limits
Part of Task 2.2.2: Система планов и ограничений (RBAC)
"""
import logging
from typing import Optional, Callable, Any
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User, SubscriptionPlan, SubscriptionStatus
from ..core.auth import get_current_user

logger = logging.getLogger(__name__)

class RBACMiddleware:
    """
    Middleware for enforcing subscription limits and feature access
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Skip middleware for certain paths
            if self._should_skip_rbac(request.url.path):
                await self.app(scope, receive, send)
                return
            
            # Check subscription limits for API endpoints
            try:
                await self._check_subscription_limits(request)
            except HTTPException as e:
                response = JSONResponse(
                    status_code=e.status_code,
                    content={"detail": e.detail, "error_code": "SUBSCRIPTION_LIMIT_EXCEEDED"}
                )
                await response(scope, receive, send)
                return
        
        await self.app(scope, receive, send)
    
    def _should_skip_rbac(self, path: str) -> bool:
        """Check if RBAC should be skipped for this path"""
        skip_paths = [
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/health",
            "/auth/login",
            "/auth/register",
            "/auth/refresh",
            "/stripe/webhook",
            "/subscription/plans",  # Allow viewing plans
        ]
        
        return any(path.startswith(skip_path) for skip_path in skip_paths)
    
    async def _check_subscription_limits(self, request: Request) -> None:
        """Check subscription limits for the current request"""
        # Get user from request (if authenticated)
        user = await self._get_user_from_request(request)
        if not user:
            return  # Skip for unauthenticated requests
        
        path = request.url.path
        method = request.method
        
        # Check API call limits
        if self._is_api_endpoint(path):
            if not user.can_make_api_call():
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"API call limit exceeded. Current plan: {user.subscription_plan.value}. "
                           f"Used: {user.api_calls_used_today}/{user.api_calls_limit} calls today."
                )
            
            # Increment API call counter
            user.increment_api_calls()
        
        # Check channel limits for channel creation
        if path.startswith("/channels") and method == "POST":
            if not user.can_add_channel():
                current_channels = len(user.channels) if user.channels else 0
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Channel limit exceeded. Current plan: {user.subscription_plan.value}. "
                           f"Used: {current_channels}/{user.channels_limit} channels."
                )
        
        # Check feature access
        feature_required = self._get_required_feature(path)
        if feature_required and not user.has_feature(feature_required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Feature '{feature_required}' not available in your current plan: {user.subscription_plan.value}. "
                       f"Please upgrade to access this feature."
            )
    
    async def _get_user_from_request(self, request: Request) -> Optional[User]:
        """Extract user from request"""
        try:
            # Get authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None
            
            # This is a simplified approach - in real implementation,
            # you'd want to properly decode the JWT token and get user
            # For now, we'll return None to skip RBAC for unauthenticated requests
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get user from request: {e}")
            return None
    
    def _is_api_endpoint(self, path: str) -> bool:
        """Check if path is an API endpoint that should count towards limits"""
        api_paths = [
            "/channels",
            "/signals", 
            "/analytics",
            "/ml/predictions",
            "/export",
        ]
        
        return any(path.startswith(api_path) for api_path in api_paths)
    
    def _get_required_feature(self, path: str) -> Optional[str]:
        """Get the feature required for accessing this path"""
        feature_map = {
            "/export": "export_data",
            "/ml/predictions": "ml_predictions",
            "/api/": "api_access",
            "/alerts/custom": "custom_alerts",
            "/support/priority": "priority_support",
        }
        
        for path_prefix, feature in feature_map.items():
            if path.startswith(path_prefix):
                return feature
        
        return None


# Dependency for checking subscription limits in route handlers
async def check_subscription_limit(
    user: User,
    feature: Optional[str] = None,
    api_call: bool = True
) -> None:
    """
    Dependency function to check subscription limits in route handlers
    
    Args:
        user: Current authenticated user
        feature: Required feature name (optional)
        api_call: Whether this counts as an API call (default: True)
    """
    # Check subscription status
    if user.subscription_status != SubscriptionStatus.ACTIVE:
        if user.subscription_status == SubscriptionStatus.EXPIRED:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Your subscription has expired. Please renew to continue using this feature."
            )
        elif user.subscription_status == SubscriptionStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Your subscription has been cancelled. Please reactivate to continue using this feature."
            )
        elif user.subscription_status == SubscriptionStatus.PAST_DUE:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Your subscription payment is past due. Please update your payment method."
            )
    
    # Check API call limits
    if api_call and not user.can_make_api_call():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"API call limit exceeded. Current plan: {user.subscription_plan.value}. "
                   f"Used: {user.api_calls_used_today}/{user.api_calls_limit} calls today. "
                   f"Upgrade to Premium or Pro for higher limits."
        )
    
    # Check feature access
    if feature and not user.has_feature(feature):
        plan_suggestions = {
            "export_data": "Premium or Pro",
            "email_notifications": "Premium or Pro", 
            "api_access": "Pro",
            "ml_predictions": "Pro",
            "custom_alerts": "Pro",
            "priority_support": "Pro"
        }
        
        suggested_plan = plan_suggestions.get(feature, "Premium or Pro")
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Feature '{feature}' is not available in your current plan ({user.subscription_plan.value}). "
                   f"Please upgrade to {suggested_plan} to access this feature."
        )
    
    # Increment API call counter if this counts as an API call
    if api_call:
        user.increment_api_calls()


# Decorator for protecting routes with subscription requirements
def require_subscription(
    plan: SubscriptionPlan = SubscriptionPlan.FREE,
    feature: Optional[str] = None
):
    """
    Decorator to require specific subscription plan or feature
    
    Args:
        plan: Minimum required subscription plan
        feature: Required feature name
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # Get user from function arguments (assumes user is passed as parameter)
            user = None
            for arg in args:
                if isinstance(arg, User):
                    user = arg
                    break
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check subscription plan
            if plan != SubscriptionPlan.FREE:
                user_plan_level = {
                    SubscriptionPlan.FREE: 0,
                    SubscriptionPlan.PREMIUM: 1,
                    SubscriptionPlan.PRO: 2
                }
                
                required_level = user_plan_level[plan]
                current_level = user_plan_level[user.subscription_plan]
                
                if current_level < required_level:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"This feature requires {plan.value} subscription. "
                               f"Current plan: {user.subscription_plan.value}"
                    )
            
            # Check feature access
            if feature:
                await check_subscription_limit(user, feature=feature, api_call=False)
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Graceful degradation helpers
class GracefulDegradation:
    """Helper class for graceful degradation of features"""
    
    @staticmethod
    def get_limited_results(user: User, full_results: list, limit_key: str) -> dict:
        """
        Return limited results based on user's subscription plan
        
        Args:
            user: Current user
            full_results: Full list of results
            limit_key: Key to identify the type of limit
        
        Returns:
            Dict with results and limitation info
        """
        limits = {
            "channels": {
                SubscriptionPlan.FREE: 3,
                SubscriptionPlan.PREMIUM: 50,
                SubscriptionPlan.PRO: None  # Unlimited
            },
            "signals": {
                SubscriptionPlan.FREE: 10,
                SubscriptionPlan.PREMIUM: 100,
                SubscriptionPlan.PRO: None  # Unlimited
            },
            "analytics": {
                SubscriptionPlan.FREE: 5,
                SubscriptionPlan.PREMIUM: 50,
                SubscriptionPlan.PRO: None  # Unlimited
            }
        }
        
        if user.is_admin or user.is_pro:
            return {
                "results": full_results,
                "limited": False,
                "total": len(full_results)
            }
        
        limit = limits.get(limit_key, {}).get(user.subscription_plan)
        if limit is None:
            return {
                "results": full_results,
                "limited": False,
                "total": len(full_results)
            }
        
        limited_results = full_results[:limit]
        return {
            "results": limited_results,
            "limited": len(full_results) > limit,
            "total": len(full_results),
            "shown": len(limited_results),
            "upgrade_message": f"Showing {len(limited_results)} of {len(full_results)} results. "
                             f"Upgrade to Premium or Pro to see all results."
        }
