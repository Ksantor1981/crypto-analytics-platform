from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionStats,
    SubscriptionUsage,
    SubscriptionCancellation,
    SubscriptionRenewal,
    SubscriptionPlanInfo
)


class SubscriptionService:
    """Service for subscription management operations."""
    
    # Plan configurations
    PLAN_CONFIGS = {
        SubscriptionPlan.FREE: {
            "name": "Free Plan",
            "description": "Basic access to crypto signals",
            "price_monthly": 0.0,
            "api_requests_limit": 100,
            "max_channels_access": 3,
            "can_access_all_channels": False,
            "can_export_data": False,
            "can_use_api": False,
            "features": [
                "Access to 3 signal channels",
                "Basic signal analytics",
                "30-day signal history",
                "100 API requests/day"
            ]
        },
        SubscriptionPlan.PREMIUM_MONTHLY: {
            "name": "Premium Monthly",
            "description": "Full access to all features",
            "price_monthly": 29.99,
            "price_yearly": None,
            "api_requests_limit": 10000,
            "max_channels_access": 999,
            "can_access_all_channels": True,
            "can_export_data": True,
            "can_use_api": True,
            "features": [
                "Access to ALL signal channels",
                "Advanced analytics & insights",
                "Unlimited signal history",
                "10,000 API requests/day",
                "Data export capabilities",
                "Premium support",
                "Real-time notifications"
            ]
        },
        SubscriptionPlan.PREMIUM_YEARLY: {
            "name": "Premium Yearly",
            "description": "Full access with yearly discount",
            "price_monthly": 24.99,
            "price_yearly": 299.99,
            "api_requests_limit": 10000,
            "max_channels_access": 999,
            "can_access_all_channels": True,
            "can_export_data": True,
            "can_use_api": True,
            "features": [
                "All Premium Monthly features",
                "2 months free (save 17%)",
                "Priority support",
                "Early access to new features"
            ]
        }
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_subscription(self, subscription_data: SubscriptionCreate) -> Subscription:
        """Create a new subscription."""
        # Verify user exists
        user = self.db.query(User).filter(User.id == subscription_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user already has an active subscription
        existing_subscription = self.db.query(Subscription).filter(
            and_(
                Subscription.user_id == subscription_data.user_id,
                Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING])
            )
        ).first()
        
        if existing_subscription:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has an active subscription"
            )
        
        # Get plan configuration
        plan_config = self.PLAN_CONFIGS.get(subscription_data.plan)
        if not plan_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid subscription plan"
            )
        
        # Create subscription
        db_subscription = Subscription(
            user_id=subscription_data.user_id,
            plan=subscription_data.plan,
            status=SubscriptionStatus.PENDING,
            price=Decimal(str(subscription_data.price)),
            currency=subscription_data.currency,
            started_at=datetime.utcnow(),
            current_period_start=subscription_data.current_period_start,
            current_period_end=subscription_data.current_period_end,
            trial_start=subscription_data.trial_start,
            trial_end=subscription_data.trial_end,
            api_requests_limit=subscription_data.api_requests_limit or plan_config["api_requests_limit"],
            can_access_all_channels=subscription_data.can_access_all_channels,
            can_export_data=subscription_data.can_export_data,
            can_use_api=subscription_data.can_use_api,
            max_channels_access=subscription_data.max_channels_access,
            auto_renew=subscription_data.auto_renew,
            stripe_price_id=subscription_data.stripe_price_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Set next billing date
        if subscription_data.plan != SubscriptionPlan.FREE:
            if subscription_data.plan == SubscriptionPlan.PREMIUM_YEARLY:
                db_subscription.next_billing_date = subscription_data.current_period_start + timedelta(days=365)
            else:
                db_subscription.next_billing_date = subscription_data.current_period_start + timedelta(days=30)
        
        self.db.add(db_subscription)
        self.db.commit()
        self.db.refresh(db_subscription)
        
        return db_subscription
    
    def get_subscription_by_id(self, subscription_id: int) -> Optional[Subscription]:
        """Get subscription by ID with user info."""
        return self.db.query(Subscription).options(joinedload(Subscription.user)).filter(
            Subscription.id == subscription_id
        ).first()
    
    def get_user_subscription(self, user_id: int) -> Optional[Subscription]:
        """Get user's current subscription."""
        return self.db.query(Subscription).filter(
            and_(
                Subscription.user_id == user_id,
                Subscription.status.in_([
                    SubscriptionStatus.ACTIVE, 
                    SubscriptionStatus.TRIALING,
                    SubscriptionStatus.PAST_DUE
                ])
            )
        ).order_by(desc(Subscription.created_at)).first()
    
    def get_subscriptions(
        self, 
        skip: int = 0, 
        limit: int = 100,
        plan: Optional[SubscriptionPlan] = None,
        status: Optional[SubscriptionStatus] = None,
        active_only: bool = False
    ) -> Tuple[List[Subscription], int]:
        """Get subscriptions with filtering and pagination."""
        query = self.db.query(Subscription).options(joinedload(Subscription.user))
        
        # Apply filters
        if plan:
            query = query.filter(Subscription.plan == plan)
        
        if status:
            query = query.filter(Subscription.status == status)
        
        if active_only:
            query = query.filter(
                Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING])
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination and sorting
        subscriptions = query.order_by(desc(Subscription.created_at)).offset(skip).limit(limit).all()
        
        return subscriptions, total
    
    def update_subscription(self, subscription_id: int, subscription_data: SubscriptionUpdate) -> Optional[Subscription]:
        """Update subscription information."""
        subscription = self.get_subscription_by_id(subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
        
        # Update fields
        update_data = subscription_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "price" and value is not None:
                setattr(subscription, field, Decimal(str(value)))
            else:
                setattr(subscription, field, value)
        
        subscription.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(subscription)
        
        return subscription
    
    def cancel_subscription(self, subscription_id: int, cancellation: SubscriptionCancellation) -> Subscription:
        """Cancel a subscription."""
        subscription = self.get_subscription_by_id(subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
        
        if subscription.status in [SubscriptionStatus.CANCELLED, SubscriptionStatus.EXPIRED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subscription is already cancelled or expired"
            )
        
        now = datetime.utcnow()
        
        if cancellation.immediate:
            # Cancel immediately
            subscription.status = SubscriptionStatus.CANCELLED
            subscription.cancelled_at = now
            subscription.ends_at = now
        else:
            # Cancel at period end
            subscription.status = SubscriptionStatus.CANCELLED
            subscription.cancelled_at = now
            subscription.ends_at = subscription.current_period_end
            subscription.auto_renew = False
        
        subscription.updated_at = now
        
        self.db.commit()
        self.db.refresh(subscription)
        
        return subscription
    
    def renew_subscription(self, subscription_id: int, renewal: SubscriptionRenewal) -> Subscription:
        """Renew a subscription."""
        subscription = self.get_subscription_by_id(subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
        
        now = datetime.utcnow()
        
        # Update plan if specified
        if renewal.plan and renewal.plan != subscription.plan:
            plan_config = self.PLAN_CONFIGS.get(renewal.plan)
            if not plan_config:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid subscription plan"
                )
            
            subscription.plan = renewal.plan
            subscription.price = Decimal(str(plan_config["price_monthly"]))
            subscription.api_requests_limit = plan_config["api_requests_limit"]
            subscription.can_access_all_channels = plan_config["can_access_all_channels"]
            subscription.can_export_data = plan_config["can_export_data"]
            subscription.can_use_api = plan_config["can_use_api"]
            subscription.max_channels_access = plan_config["max_channels_access"]
        
        # Extend subscription period
        if subscription.plan == SubscriptionPlan.PREMIUM_YEARLY:
            new_period_end = subscription.current_period_end + timedelta(days=365)
            subscription.next_billing_date = new_period_end
        else:
            new_period_end = subscription.current_period_end + timedelta(days=30)
            subscription.next_billing_date = new_period_end
        
        subscription.current_period_start = subscription.current_period_end
        subscription.current_period_end = new_period_end
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.auto_renew = renewal.auto_renew
        subscription.updated_at = now
        
        self.db.commit()
        self.db.refresh(subscription)
        
        return subscription
    
    def get_subscription_stats(self) -> SubscriptionStats:
        """Get subscription statistics."""
        # Basic counts
        total_subscriptions = self.db.query(Subscription).count()
        active_subscriptions = self.db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.ACTIVE
        ).count()
        trial_subscriptions = self.db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.TRIALING
        ).count()
        cancelled_subscriptions = self.db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.CANCELLED
        ).count()
        expired_subscriptions = self.db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.EXPIRED
        ).count()
        
        # Plan breakdown
        free_users = self.db.query(Subscription).filter(
            Subscription.plan == SubscriptionPlan.FREE
        ).count()
        premium_monthly_users = self.db.query(Subscription).filter(
            Subscription.plan == SubscriptionPlan.PREMIUM_MONTHLY
        ).count()
        premium_yearly_users = self.db.query(Subscription).filter(
            Subscription.plan == SubscriptionPlan.PREMIUM_YEARLY
        ).count()
        
        # Revenue calculation (simplified)
        monthly_revenue_query = self.db.query(func.sum(Subscription.price)).filter(
            and_(
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.plan == SubscriptionPlan.PREMIUM_MONTHLY
            )
        ).scalar() or 0
        
        yearly_revenue_query = self.db.query(func.sum(Subscription.price)).filter(
            and_(
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.plan == SubscriptionPlan.PREMIUM_YEARLY
            )
        ).scalar() or 0
        
        monthly_revenue = float(monthly_revenue_query)
        yearly_revenue = float(yearly_revenue_query) * 12  # Convert to yearly
        total_revenue = monthly_revenue + yearly_revenue
        
        # Conversion metrics (simplified)
        trial_conversion_rate = 0.0
        if trial_subscriptions > 0:
            converted_trials = self.db.query(Subscription).filter(
                and_(
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    Subscription.trial_start.isnot(None)
                )
            ).count()
            trial_conversion_rate = (converted_trials / trial_subscriptions) * 100
        
        churn_rate = 0.0
        if total_subscriptions > 0:
            churn_rate = (cancelled_subscriptions / total_subscriptions) * 100
        
        return SubscriptionStats(
            total_subscriptions=total_subscriptions,
            active_subscriptions=active_subscriptions,
            trial_subscriptions=trial_subscriptions,
            cancelled_subscriptions=cancelled_subscriptions,
            expired_subscriptions=expired_subscriptions,
            monthly_revenue=round(monthly_revenue, 2),
            yearly_revenue=round(yearly_revenue, 2),
            total_revenue=round(total_revenue, 2),
            free_users=free_users,
            premium_monthly_users=premium_monthly_users,
            premium_yearly_users=premium_yearly_users,
            trial_conversion_rate=round(trial_conversion_rate, 2),
            churn_rate=round(churn_rate, 2)
        )
    
    def get_subscription_usage(self, subscription_id: int) -> SubscriptionUsage:
        """Get subscription usage statistics."""
        subscription = self.get_subscription_by_id(subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
        
        # This is a simplified implementation
        # In a real system, you'd track actual usage from logs/metrics
        return SubscriptionUsage(
            subscription_id=subscription_id,
            api_requests_used=0,  # Would be tracked from API usage logs
            api_requests_limit=subscription.api_requests_limit,
            channels_accessed=0,  # Would be tracked from user activity
            max_channels_access=subscription.max_channels_access,
            data_exports_used=0,  # Would be tracked from export logs
            period_start=subscription.current_period_start,
            period_end=subscription.current_period_end
        )
    
    def get_available_plans(self) -> List[SubscriptionPlanInfo]:
        """Get available subscription plans."""
        plans = []
        for plan, config in self.PLAN_CONFIGS.items():
            plans.append(SubscriptionPlanInfo(
                plan=plan,
                name=config["name"],
                description=config["description"],
                price_monthly=config["price_monthly"],
                price_yearly=config.get("price_yearly"),
                features=config["features"],
                api_requests_limit=config["api_requests_limit"],
                max_channels_access=config["max_channels_access"],
                can_access_all_channels=config["can_access_all_channels"],
                can_export_data=config["can_export_data"],
                can_use_api=config["can_use_api"],
                is_popular=(plan == SubscriptionPlan.PREMIUM_MONTHLY)
            ))
        
        return plans
    
    def expire_subscriptions(self) -> int:
        """Expire subscriptions that have passed their end date."""
        now = datetime.utcnow()
        
        expired_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.CANCELLED]),
                Subscription.current_period_end <= now
            )
        ).all()
        
        for subscription in expired_subscriptions:
            subscription.status = SubscriptionStatus.EXPIRED
            subscription.updated_at = now
        
        self.db.commit()
        
        return len(expired_subscriptions) 