"""
Feedback model for user questions and suggestions
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum
from sqlalchemy.sql import func
import enum
from .base import BaseModel

class FeedbackType(enum.Enum):
    """Types of feedback"""
    QUESTION = "question"
    SUGGESTION = "suggestion"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    GENERAL = "general"

class FeedbackStatus(enum.Enum):
    """Status of feedback"""
    NEW = "new"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class Feedback(BaseModel):
    """Model for storing user feedback"""

    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)  # Optional, for anonymous feedback
    user_email = Column(String(255), nullable=True)  # Optional email for response
    user_telegram = Column(String(100), nullable=True)  # Optional Telegram username
    
    # Feedback content
    feedback_type = Column(Enum(FeedbackType), nullable=False, default=FeedbackType.GENERAL)
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Metadata
    status = Column(Enum(FeedbackStatus), nullable=False, default=FeedbackStatus.NEW)
    priority = Column(Integer, default=1)  # 1-5, where 5 is highest
    
    # Response
    admin_response = Column(Text, nullable=True)
    admin_id = Column(Integer, nullable=True)  # Admin who responded
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    responded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional info
    source = Column(String(50), default="web")  # web, telegram, api
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    
    # Tags for categorization
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    
    def __repr__(self):
        return f"<Feedback(id={self.id}, type='{self.feedback_type.value}', subject='{self.subject}')>"
