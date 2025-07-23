from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from datetime import datetime, timedelta

from app.models.user import User, UserRole
from app.models.signal import Signal
from app.schemas.user import UserCreate, UserUpdate, UserChangePassword
from app.core.security import get_password_hash, verify_password, authenticate_user


class UserService:
    """Service for user management operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        # Check if user already exists
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create new user
        db_user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=get_password_hash(user_data.password),
            role=user_data.role,
            is_active=user_data.is_active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_users(self, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[User]:
        """Get list of users with pagination."""
        query = self.db.query(User)
        if active_only:
            query = query.filter(User.is_active == True)
        
        return query.offset(skip).limit(limit).all()
    
    def get_users_count(self, active_only: bool = True) -> int:
        """Get total count of users."""
        query = self.db.query(func.count(User.id))
        if active_only:
            query = query.filter(User.is_active == True)
        
        return query.scalar()
    
    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update user information."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if email is being changed and if it's already taken
        if user_data.email and user_data.email != user.email:
            existing_user = self.get_user_by_email(user_data.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already taken"
                )
        
        # Update user fields
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def change_password(self, user_id: int, password_data: UserChangePassword) -> bool:
        """Change user password."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not verify_password(password_data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        user.hashed_password = get_password_hash(password_data.new_password)
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user account."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    def activate_user(self, user_id: int) -> bool:
        """Activate user account."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = True
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    def upgrade_subscription(self, user_id: int, role: UserRole) -> User:
        """Upgrade user role."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.role = role
        user.updated_at = datetime.utcnow()
        
        # Set subscription expiration for premium users
        if role == UserRole.PREMIUM_USER:
            user.current_subscription_expires = datetime.utcnow() + timedelta(days=30)
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def get_user_stats(self, user_id: int) -> dict:
        """Get user statistics and usage."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get real signal statistics from database
        user_signals = self.db.query(Signal).join(Channel).filter(
            Channel.owner_id == user.id
        ).all()
        
        total_signals = len(user_signals)
        successful_signals = len([s for s in user_signals if s.status == SignalStatus.COMPLETED and s.roi_percentage and s.roi_percentage > 0])
        accuracy_rate = (successful_signals / total_signals * 100) if total_signals > 0 else 0.0
        
        roi_values = [s.roi_percentage for s in user_signals if s.roi_percentage is not None]
        avg_roi = sum(roi_values) / len(roi_values) if roi_values else 0.0
        
        signals_stats = {
            "total_signals": total_signals,
            "successful_signals": successful_signals,
            "accuracy_rate": round(accuracy_rate, 1),
            "avg_roi": round(avg_roi, 2)
        }
        
        return signals_stats
        
        return stats
    
    def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate user by email and password."""
        return authenticate_user(self.db, email, password)
    
    def is_email_available(self, email: str) -> bool:
        """Check if email is available for registration."""
        user = self.get_user_by_email(email)
        return user is None
    
    def delete_user(self, user_id: int) -> bool:
        """Delete user account (admin only)."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        self.db.delete(user)
        self.db.commit()
        return True 