"""
API Key Management Endpoints - Pro feature
Part of Task 2.3.2: Pro функции
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...database import get_db
from ...models.user import User
from ...core.auth import get_current_user
from ...services.api_key_service import api_key_service
from ...middleware.rbac_middleware import require_subscription_plan, SubscriptionPlan

router = APIRouter()

class CreateAPIKeyRequest(BaseModel):
    name: str
    expires_in_days: Optional[int] = 365
    permissions: Optional[Dict[str, bool]] = None
    rate_limits: Optional[Dict[str, int]] = None

class UpdateAPIKeyRequest(BaseModel):
    name: Optional[str] = None
    permissions: Optional[Dict[str, bool]] = None
    rate_limits: Optional[Dict[str, int]] = None

@router.post("/api-keys")
async def create_api_key(
    request: CreateAPIKeyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new API key
    Pro feature - requires Pro subscription
    """
    # Check subscription level
    await require_subscription_plan(current_user, SubscriptionPlan.PRO)
    
    try:
        api_key_data = await api_key_service.create_api_key(
            user=current_user,
            db=db,
            name=request.name,
            permissions=request.permissions,
            expires_in_days=request.expires_in_days,
            rate_limits=request.rate_limits
        )
        
        return {
            "success": True,
            "message": "API key created successfully",
            "data": api_key_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}"
        )

@router.get("/api-keys")
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all API keys for the current user
    Pro feature - requires Pro subscription
    """
    # Check subscription level
    await require_subscription_plan(current_user, SubscriptionPlan.PRO)
    
    try:
        keys = await api_key_service.list_api_keys(current_user, db)
        
        return {
            "success": True,
            "data": keys,
            "total": len(keys)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve API keys: {str(e)}"
        )

@router.put("/api-keys/{key_id}")
async def update_api_key(
    key_id: int,
    request: UpdateAPIKeyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an API key
    Pro feature - requires Pro subscription
    """
    # Check subscription level
    await require_subscription_plan(current_user, SubscriptionPlan.PRO)
    
    try:
        updated_key = await api_key_service.update_api_key(
            user=current_user,
            db=db,
            key_id=key_id,
            name=request.name,
            permissions=request.permissions,
            rate_limits=request.rate_limits
        )
        
        return {
            "success": True,
            "message": "API key updated successfully",
            "data": updated_key
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update API key: {str(e)}"
        )

@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke an API key
    Pro feature - requires Pro subscription
    """
    # Check subscription level
    await require_subscription_plan(current_user, SubscriptionPlan.PRO)
    
    try:
        success = await api_key_service.revoke_api_key(current_user, db, key_id)
        
        return {
            "success": success,
            "message": "API key revoked successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke API key: {str(e)}"
        )

@router.get("/api-keys/usage")
async def get_api_usage_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get API usage statistics
    Pro feature - requires Pro subscription
    """
    # Check subscription level
    await require_subscription_plan(current_user, SubscriptionPlan.PRO)
    
    try:
        stats = await api_key_service.get_api_usage_stats(current_user, db)
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve usage stats: {str(e)}"
        )

@router.get("/api-keys/permissions")
async def get_available_permissions(
    current_user: User = Depends(get_current_user)
):
    """
    Get list of available API permissions for Pro users
    """
    # Check subscription level
    await require_subscription_plan(current_user, SubscriptionPlan.PRO)
    
    return {
        "success": True,
        "data": {
            "permissions": {
                "can_read_channels": {
                    "description": "Read access to user's channels",
                    "default": True
                },
                "can_read_signals": {
                    "description": "Read access to crypto signals",
                    "default": True
                },
                "can_read_analytics": {
                    "description": "Read access to analytics data",
                    "default": True
                },
                "can_export_data": {
                    "description": "Export data in various formats",
                    "default": True
                }
            },
            "rate_limits": {
                "requests_per_day": {
                    "description": "Maximum requests per day",
                    "default": 10000,
                    "max": 50000
                },
                "requests_per_hour": {
                    "description": "Maximum requests per hour",
                    "default": 1000,
                    "max": 5000
                }
            }
        }
    }
