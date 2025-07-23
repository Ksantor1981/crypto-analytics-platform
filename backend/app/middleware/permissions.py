from fastapi import Depends, HTTPException, status
from typing import List

from app.models.user import User, UserRole
from app.api.deps import get_current_active_user

class RoleChecker:
    """
    Dependency to check user roles. 
    It can be used like: Depends(RoleChecker([UserRole.ADMIN]))
    """
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_active_user)):
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user does not have adequate permissions to access this resource."
            )
        return user
