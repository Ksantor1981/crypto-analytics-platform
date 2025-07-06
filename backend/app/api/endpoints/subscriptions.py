from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from math import ceil

from app.core.database import get_db
from app.core.auth import (
    get_current_active_user,
    require_admin,
    require_premium
)
from app.services.subscription_service import SubscriptionService
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionResponse,
    SubscriptionWithUser,
    SubscriptionListResponse,
    SubscriptionStats,
    SubscriptionUsage,
    SubscriptionCancellation,
    SubscriptionRenewal,
    SubscriptionPlanInfo,
    SubscriptionPlan,
    SubscriptionStatus
)
from app.models.user import User

router = APIRouter()


@router.get("/plans", response_model=List[SubscriptionPlanInfo])
async def get_subscription_plans():
    """Get available subscription plans."""
    subscription_service = SubscriptionService(None)  # No DB needed for static data
    
    plans = subscription_service.get_available_plans()
    
    return plans


@router.get("/me", response_model=Optional[SubscriptionResponse])
async def get_my_subscription(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's subscription."""
    subscription_service = SubscriptionService(db)
    
    subscription = subscription_service.get_user_subscription(current_user.id)
    
    if not subscription:
        return None
    
    return SubscriptionResponse.from_orm(subscription)


@router.post("/", response_model=SubscriptionResponse)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new subscription for current user."""
    subscription_service = SubscriptionService(db)
    
    # Override user_id with current user
    subscription_data.user_id = current_user.id
    
    subscription = subscription_service.create_subscription(subscription_data)
    
    return SubscriptionResponse.from_orm(subscription)


@router.put("/me", response_model=SubscriptionResponse)
async def update_my_subscription(
    subscription_data: SubscriptionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user's subscription."""
    subscription_service = SubscriptionService(db)
    
    # Get user's current subscription
    subscription = subscription_service.get_user_subscription(current_user.id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    updated_subscription = subscription_service.update_subscription(subscription.id, subscription_data)
    
    return SubscriptionResponse.from_orm(updated_subscription)


@router.post("/me/cancel", response_model=SubscriptionResponse)
async def cancel_my_subscription(
    cancellation: SubscriptionCancellation,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cancel current user's subscription."""
    subscription_service = SubscriptionService(db)
    
    # Get user's current subscription
    subscription = subscription_service.get_user_subscription(current_user.id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    cancelled_subscription = subscription_service.cancel_subscription(subscription.id, cancellation)
    
    return SubscriptionResponse.from_orm(cancelled_subscription)


@router.post("/me/renew", response_model=SubscriptionResponse)
async def renew_my_subscription(
    renewal: SubscriptionRenewal,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Renew current user's subscription."""
    subscription_service = SubscriptionService(db)
    
    # Get user's current subscription
    subscription = subscription_service.get_user_subscription(current_user.id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    renewed_subscription = subscription_service.renew_subscription(subscription.id, renewal)
    
    return SubscriptionResponse.from_orm(renewed_subscription)


@router.get("/me/usage", response_model=SubscriptionUsage)
async def get_my_subscription_usage(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's subscription usage."""
    subscription_service = SubscriptionService(db)
    
    # Get user's current subscription
    subscription = subscription_service.get_user_subscription(current_user.id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    usage = subscription_service.get_subscription_usage(subscription.id)
    
    return usage


# Admin endpoints
@router.get("/", response_model=SubscriptionListResponse, dependencies=[Depends(require_admin)])
async def get_subscriptions(
    skip: int = Query(0, ge=0, description="Number of subscriptions to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of subscriptions to return"),
    plan: Optional[SubscriptionPlan] = Query(None, description="Filter by plan"),
    status: Optional[SubscriptionStatus] = Query(None, description="Filter by status"),
    active_only: bool = Query(False, description="Show only active subscriptions"),
    db: Session = Depends(get_db)
):
    """Get all subscriptions (admin only)."""
    subscription_service = SubscriptionService(db)
    
    subscriptions, total = subscription_service.get_subscriptions(
        skip=skip,
        limit=limit,
        plan=plan,
        status=status,
        active_only=active_only
    )
    
    # Calculate pagination
    pages = ceil(total / limit) if total > 0 else 0
    page = (skip // limit) + 1
    
    # Convert to response format with user info
    subscription_responses = []
    for subscription in subscriptions:
        subscription_dict = SubscriptionWithUser.from_orm(subscription).dict()
        if subscription.user:
            subscription_dict["user_email"] = subscription.user.email
            subscription_dict["user_name"] = subscription.user.full_name
        subscription_responses.append(SubscriptionWithUser(**subscription_dict))
    
    return SubscriptionListResponse(
        subscriptions=subscription_responses,
        total=total,
        page=page,
        size=limit,
        pages=pages
    )


@router.get("/{subscription_id}", response_model=SubscriptionWithUser, dependencies=[Depends(require_admin)])
async def get_subscription(
    subscription_id: int,
    db: Session = Depends(get_db)
):
    """Get subscription by ID (admin only)."""
    subscription_service = SubscriptionService(db)
    
    subscription = subscription_service.get_subscription_by_id(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Convert to response with user info
    subscription_dict = SubscriptionWithUser.from_orm(subscription).dict()
    if subscription.user:
        subscription_dict["user_email"] = subscription.user.email
        subscription_dict["user_name"] = subscription.user.full_name
    
    return SubscriptionWithUser(**subscription_dict)


@router.post("/admin/create", response_model=SubscriptionResponse, dependencies=[Depends(require_admin)])
async def create_subscription_admin(
    subscription_data: SubscriptionCreate,
    db: Session = Depends(get_db)
):
    """Create a subscription for any user (admin only)."""
    subscription_service = SubscriptionService(db)
    
    subscription = subscription_service.create_subscription(subscription_data)
    
    return SubscriptionResponse.from_orm(subscription)


@router.put("/{subscription_id}", response_model=SubscriptionResponse, dependencies=[Depends(require_admin)])
async def update_subscription(
    subscription_id: int,
    subscription_data: SubscriptionUpdate,
    db: Session = Depends(get_db)
):
    """Update subscription (admin only)."""
    subscription_service = SubscriptionService(db)
    
    subscription = subscription_service.update_subscription(subscription_id, subscription_data)
    
    return SubscriptionResponse.from_orm(subscription)


@router.post("/{subscription_id}/cancel", response_model=SubscriptionResponse, dependencies=[Depends(require_admin)])
async def cancel_subscription(
    subscription_id: int,
    cancellation: SubscriptionCancellation,
    db: Session = Depends(get_db)
):
    """Cancel subscription (admin only)."""
    subscription_service = SubscriptionService(db)
    
    subscription = subscription_service.cancel_subscription(subscription_id, cancellation)
    
    return SubscriptionResponse.from_orm(subscription)


@router.post("/{subscription_id}/renew", response_model=SubscriptionResponse, dependencies=[Depends(require_admin)])
async def renew_subscription(
    subscription_id: int,
    renewal: SubscriptionRenewal,
    db: Session = Depends(get_db)
):
    """Renew subscription (admin only)."""
    subscription_service = SubscriptionService(db)
    
    subscription = subscription_service.renew_subscription(subscription_id, renewal)
    
    return SubscriptionResponse.from_orm(subscription)


@router.get("/stats/overview", response_model=SubscriptionStats, dependencies=[Depends(require_admin)])
async def get_subscription_stats(db: Session = Depends(get_db)):
    """Get subscription statistics (admin only)."""
    subscription_service = SubscriptionService(db)
    
    stats = subscription_service.get_subscription_stats()
    
    return stats


@router.get("/{subscription_id}/usage", response_model=SubscriptionUsage, dependencies=[Depends(require_admin)])
async def get_subscription_usage(
    subscription_id: int,
    db: Session = Depends(get_db)
):
    """Get subscription usage (admin only)."""
    subscription_service = SubscriptionService(db)
    
    usage = subscription_service.get_subscription_usage(subscription_id)
    
    return usage


@router.post("/maintenance/expire", dependencies=[Depends(require_admin)])
async def expire_old_subscriptions(db: Session = Depends(get_db)):
    """Expire subscriptions that have passed their end date (admin only)."""
    subscription_service = SubscriptionService(db)
    
    expired_count = subscription_service.expire_subscriptions()
    
    return {"message": f"Expired {expired_count} subscriptions"}


# Premium user endpoints
@router.get("/premium/features", dependencies=[Depends(require_premium)])
async def get_premium_features(
    current_user: User = Depends(require_premium),
    db: Session = Depends(get_db)
):
    """Get premium features available to user."""
    subscription_service = SubscriptionService(db)
    
    subscription = subscription_service.get_user_subscription(current_user.id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    return {
        "plan": subscription.plan,
        "features": {
            "api_requests_limit": subscription.api_requests_limit,
            "can_access_all_channels": subscription.can_access_all_channels,
            "can_export_data": subscription.can_export_data,
            "can_use_api": subscription.can_use_api,
            "max_channels_access": subscription.max_channels_access
        },
        "subscription_status": subscription.status,
        "expires_at": subscription.current_period_end,
        "auto_renew": subscription.auto_renew
    } 