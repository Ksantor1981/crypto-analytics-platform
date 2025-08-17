"""
Feedback API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend.app.core.database import get_db
from backend.app.models.feedback import Feedback, FeedbackType, FeedbackStatus
from backend.app.schemas.feedback import (
    FeedbackCreate, FeedbackRead, FeedbackUpdate, FeedbackResponse,
    FeedbackList, FeedbackStats
)
from backend.app.core.auth import get_current_user_optional
from backend.app.models.user import User

router = APIRouter()

@router.post("/", response_model=FeedbackRead, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    feedback: FeedbackCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Create new feedback"""
    
    # Get client info
    user_agent = request.headers.get("user-agent", "")
    ip_address = request.client.host if request.client else None
    
    # Create feedback object
    db_feedback = Feedback(
        user_id=current_user.id if current_user else None,
        user_email=feedback.user_email,
        user_telegram=feedback.user_telegram,
        feedback_type=feedback.feedback_type,
        subject=feedback.subject,
        message=feedback.message,
        tags=feedback.tags,
        source="web",
        user_agent=user_agent,
        ip_address=ip_address
    )
    
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    
    return db_feedback

@router.get("/", response_model=FeedbackList)
async def get_feedback_list(
    page: int = 1,
    per_page: int = 20,
    status_filter: Optional[FeedbackStatus] = None,
    type_filter: Optional[FeedbackType] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """Get feedback list with pagination"""
    
    if not current_user or not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Build query
    query = db.query(Feedback)
    
    if status_filter:
        query = query.filter(Feedback.status == status_filter)
    
    if type_filter:
        query = query.filter(Feedback.feedback_type == type_filter)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * per_page
    feedbacks = query.order_by(Feedback.created_at.desc()).offset(offset).limit(per_page).all()
    
    total_pages = (total + per_page - 1) // per_page
    
    return FeedbackList(
        feedbacks=feedbacks,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

@router.get("/{feedback_id}", response_model=FeedbackRead)
async def get_feedback(
    feedback_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """Get specific feedback by ID"""
    
    if not current_user or not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )
    
    return feedback

@router.put("/{feedback_id}", response_model=FeedbackRead)
async def update_feedback(
    feedback_id: int,
    feedback_update: FeedbackUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """Update feedback (admin only)"""
    
    if not current_user or not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )
    
    # Update fields
    update_data = feedback_update.dict(exclude_unset=True)
    
    # Set responded_at if admin_response is provided
    if "admin_response" in update_data and update_data["admin_response"]:
        update_data["responded_at"] = datetime.utcnow()
        update_data["admin_id"] = current_user.id
    
    for field, value in update_data.items():
        setattr(feedback, field, value)
    
    db.commit()
    db.refresh(feedback)
    
    return feedback

@router.post("/{feedback_id}/respond", response_model=FeedbackRead)
async def respond_to_feedback(
    feedback_id: int,
    response: FeedbackResponse,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """Respond to feedback (admin only)"""
    
    if not current_user or not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )
    
    # Update feedback with response
    feedback.admin_response = response.admin_response
    feedback.status = response.status
    feedback.admin_id = current_user.id
    feedback.responded_at = datetime.utcnow()
    
    db.commit()
    db.refresh(feedback)
    
    return feedback

@router.get("/stats/overview", response_model=FeedbackStats)
async def get_feedback_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """Get feedback statistics (admin only)"""
    
    if not current_user or not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get counts by status
    total_feedback = db.query(Feedback).count()
    new_feedback = db.query(Feedback).filter(Feedback.status == FeedbackStatus.NEW).count()
    in_progress = db.query(Feedback).filter(Feedback.status == FeedbackStatus.IN_PROGRESS).count()
    resolved = db.query(Feedback).filter(Feedback.status == FeedbackStatus.RESOLVED).count()
    closed = db.query(Feedback).filter(Feedback.status == FeedbackStatus.CLOSED).count()
    
    # Get counts by type
    by_type = {}
    for feedback_type in FeedbackType:
        count = db.query(Feedback).filter(Feedback.feedback_type == feedback_type).count()
        by_type[feedback_type.value] = count
    
    # Get counts by priority
    by_priority = {}
    for priority in range(1, 6):
        count = db.query(Feedback).filter(Feedback.priority == priority).count()
        by_priority[str(priority)] = count
    
    return FeedbackStats(
        total_feedback=total_feedback,
        new_feedback=new_feedback,
        in_progress=in_progress,
        resolved=resolved,
        closed=closed,
        by_type=by_type,
        by_priority=by_priority
    )

@router.delete("/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feedback(
    feedback_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """Delete feedback (admin only)"""
    
    if not current_user or not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )
    
    db.delete(feedback)
    db.commit()
    
    return None
