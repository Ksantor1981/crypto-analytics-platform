"""
Export API Endpoints - Premium feature
Part of Task 2.3.1: Premium функции
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.core.auth import get_current_user
from app.middleware.rbac_middleware import check_subscription_limit

try:
    from app.services.export_service import export_service
except ImportError:
    export_service = None

router = APIRouter()


async def _ensure_export_access(user: User) -> None:
    """Premium/Pro: фича export_data (см. User.has_feature)."""
    await check_subscription_limit(user, feature="export_data", api_call=False)

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
    if export_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Export service unavailable",
        )
    await _ensure_export_access(current_user)

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
    if export_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Export service unavailable",
        )
    await _ensure_export_access(current_user)

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
    if export_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Export service unavailable",
        )
    await _ensure_export_access(current_user)

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
    if export_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Export service unavailable",
        )
    await _ensure_export_access(current_user)

    return {
        "supported_formats": export_service.supported_formats,
        "export_types": ["signals", "channels", "analytics"],
        "description": {
            "csv": "Comma-separated values format",
            "excel": "Microsoft Excel format with multiple sheets",
            "json": "JavaScript Object Notation format"
        }
    }
