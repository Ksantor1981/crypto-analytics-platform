from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from math import ceil
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.database import get_db
from app.core.auth import (
    get_current_user, 
    get_current_active_user, 
    get_current_admin_user,
    require_admin,
    require_premium
)
from app.core.security import create_user_tokens, verify_token
from app.core.rate_limiter import limiter, get_auth_rate_limit
from app.core.logging import log_authentication_attempt, log_security_event, get_logger
from app.services.user_service import UserService
from app import schemas
from app.models.user import User

router = APIRouter()
logger = get_logger(__name__)


@router.post("/register", response_model=schemas.user.UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(get_auth_rate_limit())
async def register_user(
    request: Request,
    user_data: schemas.user.UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    client_ip = get_remote_address(request)
    user_agent = request.headers.get("user-agent", "")
    
    try:
        user_service = UserService(db)
        
        # Create user
        user = user_service.create_user(user_data)
        
        logger.info(
            "User registered successfully",
            user_id=user.id,
            email=user.email,
            ip=client_ip
        )
        
        return schemas.user.UserResponse.from_orm(user)
        
    except Exception as e:
        logger.error(
            "User registration failed",
            email=user_data.email,
            ip=client_ip,
            error=str(e)
        )
        raise


@router.post("/login", response_model=schemas.user.TokenResponse)
@limiter.limit(get_auth_rate_limit())
async def login_user(
    request: Request,
    user_data: schemas.user.UserLogin,
    db: Session = Depends(get_db)
):
    """Login user and return JWT tokens."""
    client_ip = get_remote_address(request)
    user_agent = request.headers.get("user-agent", "")
    
    try:
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Login error",
            email=user_data.email,
            ip=client_ip,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit(get_auth_rate_limit())
async def refresh_token(
    request: Request,
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    client_ip = get_remote_address(request)
    
    try:
        # Verify refresh token
        payload = verify_token(token_data.refresh_token, token_type="refresh")
        user_id = payload.get("sub")
        
        if user_id is None:
            log_security_event(
                "invalid_refresh_token",
                user_id=None,
                ip_address=client_ip,
                details={}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user and create new tokens
        user_service = UserService(db)
        user = user_service.get_user_by_id(int(user_id))
        
        if not user or not user.is_active:
            log_security_event(
                "refresh_token_for_inactive_user",
                user_id=int(user_id) if user_id else None,
                ip_address=client_ip,
                details={"user_id": user_id}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create new tokens
        tokens = create_user_tokens(user)
        
        logger.info(
            "Token refreshed successfully",
            user_id=user.id,
            ip=client_ip
        )
        
        return TokenResponse(**tokens)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Token refresh error",
            ip=client_ip,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


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
    
    try:
        # Update user
        updated_user = user_service.update_user(current_user.id, user_data)
        
        logger.info(
            "User profile updated",
            user_id=current_user.id,
            email=current_user.email
        )
        
        return UserResponse.from_orm(updated_user)
        
    except Exception as e:
        logger.error(
            "User profile update failed",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


@router.post("/me/change-password")
@limiter.limit(get_auth_rate_limit())
async def change_current_user_password(
    request: Request,
    password_data: UserChangePassword,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change current user password."""
    client_ip = get_remote_address(request)
    user_service = UserService(db)
    
    try:
        # Change password
        success = user_service.change_password(current_user.id, password_data)
        
        if success:
            log_security_event(
                "password_changed",
                user_id=current_user.id,
                ip_address=client_ip,
                details={}
            )
            return {"message": "Password changed successfully"}
        else:
            log_security_event(
                "password_change_failed",
                user_id=current_user.id,
                ip_address=client_ip,
                details={}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to change password"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Password change error",
            user_id=current_user.id,
            ip=client_ip,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
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
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Deactivate current user account."""
    client_ip = get_remote_address(request)
    user_service = UserService(db)
    
    try:
        # Deactivate user
        success = user_service.deactivate_user(current_user.id)
        
        if success:
            log_security_event(
                "user_deactivated",
                user_id=current_user.id,
                ip_address=client_ip,
                details={}
            )
            return {"message": "Account deactivated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to deactivate account"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Account deactivation error",
            user_id=current_user.id,
            ip=client_ip,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Account deactivation failed"
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
    
    # Get users and total count
    users, total = user_service.get_users(skip=skip, limit=limit, active_only=active_only)
    
    # Calculate pagination
    total_pages = ceil(total / limit)
    current_page = (skip // limit) + 1
    
    return UserListResponse(
        users=[UserResponse.from_orm(user) for user in users],
        total=total,
        page=current_page,
        pages=total_pages,
        per_page=limit
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
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.from_orm(updated_user)


@router.post("/{user_id}/activate", dependencies=[Depends(require_admin)])
async def activate_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Activate user (admin only)."""
    user_service = UserService(db)
    
    success = user_service.activate_user(user_id)
    if success:
        return {"message": "User activated successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.post("/{user_id}/deactivate", dependencies=[Depends(require_admin)])
async def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Deactivate user (admin only)."""
    user_service = UserService(db)
    
    success = user_service.deactivate_user(user_id)
    if success:
        return {"message": "User deactivated successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.post("/{user_id}/upgrade", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def upgrade_user_subscription(
    user_id: int,
    role: UserRole,
    db: Session = Depends(get_db)
):
    """Upgrade user subscription (admin only)."""
    user_service = UserService(db)
    
    updated_user = user_service.upgrade_user_subscription(user_id, role)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.from_orm(updated_user)


@router.delete("/{user_id}", dependencies=[Depends(require_admin)])
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Delete user (admin only)."""
    user_service = UserService(db)
    
    success = user_service.delete_user(user_id)
    if success:
        return {"message": "User deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.get("/{user_id}/stats", response_model=UserStats, dependencies=[Depends(require_admin)])
async def get_user_stats_by_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user statistics by ID (admin only)."""
    user_service = UserService(db)
    
    stats = user_service.get_user_stats(user_id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserStats(**stats) 