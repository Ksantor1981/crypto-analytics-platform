"""
Feedback schemas for API
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

class FeedbackType(str, Enum):
    """Types of feedback"""
    QUESTION = "question"
    SUGGESTION = "suggestion"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    GENERAL = "general"

class FeedbackStatus(str, Enum):
    """Status of feedback"""
    NEW = "new"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class FeedbackCreate(BaseModel):
    """Schema for creating feedback"""
    feedback_type: FeedbackType = Field(default=FeedbackType.GENERAL, description="Type of feedback")
    subject: str = Field(..., min_length=1, max_length=200, description="Subject of feedback")
    message: str = Field(..., min_length=10, max_length=5000, description="Feedback message")
    user_email: Optional[EmailStr] = Field(None, description="Email for response (optional)")
    user_telegram: Optional[str] = Field(None, max_length=100, description="Telegram username (optional)")
    tags: Optional[str] = Field(None, max_length=500, description="Comma-separated tags")

class FeedbackResponse(BaseModel):
    """Schema for admin response to feedback"""
    admin_response: str = Field(..., min_length=1, max_length=5000, description="Admin response")
    status: FeedbackStatus = Field(default=FeedbackStatus.RESOLVED, description="New status")

class FeedbackUpdate(BaseModel):
    """Schema for updating feedback"""
    status: Optional[FeedbackStatus] = Field(None, description="New status")
    priority: Optional[int] = Field(None, ge=1, le=5, description="Priority (1-5)")
    admin_response: Optional[str] = Field(None, max_length=5000, description="Admin response")
    tags: Optional[str] = Field(None, max_length=500, description="Comma-separated tags")

class FeedbackRead(BaseModel):
    """Schema for reading feedback"""
    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    user_telegram: Optional[str] = None
    feedback_type: FeedbackType
    subject: str
    message: str
    status: FeedbackStatus
    priority: int
    admin_response: Optional[str] = None
    admin_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    source: str
    tags: Optional[str] = None

    class Config:
        from_attributes = True

class FeedbackList(BaseModel):
    """Schema for feedback list with pagination"""
    feedbacks: List[FeedbackRead]
    total: int
    page: int
    per_page: int
    total_pages: int

class FeedbackStats(BaseModel):
    """Schema for feedback statistics"""
    total_feedback: int
    new_feedback: int
    in_progress: int
    resolved: int
    closed: int
    by_type: dict[str, int]
    by_priority: dict[str, int]
