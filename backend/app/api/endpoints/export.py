"""
Export API Endpoints - Premium feature
Part of Task 2.3.1: Premium функции
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.user import User
from ...core.auth import get_current_user
from ...services.export_service import export_service
from ...middleware.rbac_middleware import require_subscription_plan, SubscriptionPlan

router = APIRouter()

@router.get("/export/signals")
async def export_signals(
    format: str = Query("csv", description="Export format: csv, excel, json"),
    date_from: Optional[datetime] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[datetime] = Query(None, description="End date (YYYY-MM-DD)"),
    channel_ids: Optional[List[str]] = Query(None, description="Specific channel IDs"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    Export user's crypto signals data
    Premium feature - requires Premium or Pro subscription
    """
    # Check subscription level
    await require_subscription_plan(current_user, SubscriptionPlan.PREMIUM)
    
    try:
        return await export_service.export_user_data(
            user=current_user,
            db=db,
            export_type='signals',
            format=format,
            date_from=date_from,
            date_to=date_to,
            channel_ids=channel_ids
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )

@router.get("/export/channels")
async def export_channels(
    format: str = Query("csv", description="Export format: csv, excel, json"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    Export user's channels data
    Premium feature - requires Premium or Pro subscription
    """
    # Check subscription level
    await require_subscription_plan(current_user, SubscriptionPlan.PREMIUM)
    
    try:
        return await export_service.export_user_data(
            user=current_user,
            db=db,
            export_type='channels',
            format=format
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )

@router.get("/export/analytics")
async def export_analytics(
    format: str = Query("csv", description="Export format: csv, excel, json"),
    date_from: Optional[datetime] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[datetime] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    Export user's analytics data
    Premium feature - requires Premium or Pro subscription
    """
    # Check subscription level
    await require_subscription_plan(current_user, SubscriptionPlan.PREMIUM)
    
    try:
        return await export_service.export_user_data(
            user=current_user,
            db=db,
            export_type='analytics',
            format=format,
            date_from=date_from,
            date_to=date_to
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )

@router.get("/export/formats")
async def get_supported_formats(
    current_user: User = Depends(get_current_user)
):
    """
    Get list of supported export formats
    Premium feature - requires Premium or Pro subscription
    """
    # Check subscription level
    await require_subscription_plan(current_user, SubscriptionPlan.PREMIUM)
    
    return {
        "supported_formats": export_service.supported_formats,
        "export_types": ["signals", "channels", "analytics"],
        "description": {
            "csv": "Comma-separated values format",
            "excel": "Microsoft Excel format with multiple sheets",
            "json": "JavaScript Object Notation format"
        }
    }
