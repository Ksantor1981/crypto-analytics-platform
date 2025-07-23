"""
Custom Alert Model - Database model for user custom alerts
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base

class CustomAlert(Base):
    """Model for custom user alerts"""
    __tablename__ = "custom_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Alert configuration
    name = Column(String(255), nullable=True)
    alert_type = Column(String(50), nullable=False)  # signal_confidence, price_threshold, portfolio_change
    conditions = Column(JSON, nullable=False)  # Alert conditions as JSON
    notification_methods = Column(JSON, nullable=False)  # email, webhook, etc.
    webhook_url = Column(String(500), nullable=True)
    
    # Status and tracking
    is_active = Column(Boolean, default=True, nullable=False)
    triggered_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_triggered_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="custom_alerts")
    
    def __repr__(self):
        return f"<CustomAlert(id={self.id}, user_id={self.user_id}, type={self.alert_type})>"
