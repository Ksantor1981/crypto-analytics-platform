from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from math import ceil

from app.core.database import get_db
from app.core.auth import (
    get_current_user, 
    get_current_active_user, 
    get_current_admin_user,
    require_admin,
    require_premium
)
from app.core.security import create_user_tokens, verify_token
from app.services.user_service import UserService
from app.schemas.user import (
    UserCreate, 
    UserResponse, 
    UserLogin, 
    TokenResponse,
    TokenRefresh,
    UserUpdate,
    UserChangePassword,
    UserProfile,
    UserStats,
    UserListResponse,
    UserRole
)
from app.models.user import User

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    user_service = UserService(db)
    
    # Create user
    user = user_service.create_user(user_data)
    
    return UserResponse.from_orm(user)


@router.post("/login", response_model=TokenResponse)
async def login_user(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Login user and return JWT tokens."""
    user_service = UserService(db)
    
    # Authenticate user
    user = user_service.authenticate(user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    tokens = create_user_tokens(user)
    
    return TokenResponse(**tokens)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    # Verify refresh token
    payload = verify_token(token_data.refresh_token, token_type="refresh")
    user_id = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user and create new tokens
    user_service = UserService(db)
    user = user_service.get_user_by_id(int(user_id))
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new tokens
    tokens = create_user_tokens(user)
    
    return TokenResponse(**tokens)


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user profile."""
    return UserProfile.from_orm(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user profile."""
    user_service = UserService(db)
    
    # Update user
    updated_user = user_service.update_user(current_user.id, user_data)
    
    return UserResponse.from_orm(updated_user)


@router.post("/me/change-password")
async def change_current_user_password(
    password_data: UserChangePassword,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change current user password."""
    user_service = UserService(db)
    
    # Change password
    success = user_service.change_password(current_user.id, password_data)
    
    if success:
        return {"message": "Password changed successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to change password"
        )


@router.get("/me/stats", response_model=UserStats)
async def get_current_user_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user statistics."""
    user_service = UserService(db)
    
    # Get user stats
    stats = user_service.get_user_stats(current_user.id)
    
    return UserStats(**stats)


@router.post("/me/deactivate")
async def deactivate_current_user(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Deactivate current user account."""
    user_service = UserService(db)
    
    # Deactivate user
    success = user_service.deactivate_user(current_user.id)
    
    if success:
        return {"message": "Account deactivated successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to deactivate account"
        )


# Admin endpoints
@router.get("/", response_model=UserListResponse, dependencies=[Depends(require_admin)])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Get list of users (admin only)."""
    user_service = UserService(db)
    
    # Get users and count
    users = user_service.get_users(skip=skip, limit=limit, active_only=active_only)
    total = user_service.get_users_count(active_only=active_only)
    
    # Calculate pagination
    pages = ceil(total / limit) if total > 0 else 0
    page = (skip // limit) + 1
    
    return UserListResponse(
        users=[UserResponse.from_orm(user) for user in users],
        total=total,
        page=page,
        size=limit,
        pages=pages
    )


@router.get("/{user_id}", response_model=UserProfile, dependencies=[Depends(require_admin)])
async def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user by ID (admin only)."""
    user_service = UserService(db)
    
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserProfile.from_orm(user)


@router.put("/{user_id}", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def update_user_by_id(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db)
):
    """Update user by ID (admin only)."""
    user_service = UserService(db)
    
    updated_user = user_service.update_user(user_id, user_data)
    
    return UserResponse.from_orm(updated_user)


@router.post("/{user_id}/activate", dependencies=[Depends(require_admin)])
async def activate_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Activate user account (admin only)."""
    user_service = UserService(db)
    
    success = user_service.activate_user(user_id)
    
    if success:
        return {"message": "User activated successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to activate user"
        )


@router.post("/{user_id}/deactivate", dependencies=[Depends(require_admin)])
async def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Deactivate user account (admin only)."""
    user_service = UserService(db)
    
    success = user_service.deactivate_user(user_id)
    
    if success:
        return {"message": "User deactivated successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to deactivate user"
        )


@router.post("/{user_id}/upgrade", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def upgrade_user_subscription(
    user_id: int,
    role: UserRole,
    db: Session = Depends(get_db)
):
    """Upgrade user role (admin only)."""
    user_service = UserService(db)
    
    updated_user = user_service.upgrade_subscription(user_id, role)
    
    return UserResponse.from_orm(updated_user)


@router.delete("/{user_id}", dependencies=[Depends(require_admin)])
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Delete user account (admin only)."""
    user_service = UserService(db)
    
    success = user_service.delete_user(user_id)
    
    if success:
        return {"message": "User deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete user"
        )


@router.get("/{user_id}/stats", response_model=UserStats, dependencies=[Depends(require_admin)])
async def get_user_stats_by_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user statistics by ID (admin only)."""
    user_service = UserService(db)
    
    stats = user_service.get_user_stats(user_id)
    
    return UserStats(**stats) 