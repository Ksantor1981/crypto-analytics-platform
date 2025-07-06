"""
Rate limiting utilities for API protection
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException, status
import structlog

from .config import settings

logger = structlog.get_logger(__name__)

# Create limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_REQUESTS}/hour"]
)

def get_auth_rate_limit() -> str:
    """Get authentication rate limit string."""
    return f"{settings.AUTH_RATE_LIMIT_REQUESTS}/{settings.AUTH_RATE_LIMIT_WINDOW}seconds"

def get_general_rate_limit() -> str:
    """Get general rate limit string."""
    return f"{settings.RATE_LIMIT_REQUESTS}/{settings.RATE_LIMIT_WINDOW}seconds"

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit exceeded handler."""
    client_ip = get_remote_address(request)
    
    logger.warning(
        "Rate limit exceeded",
        client_ip=client_ip,
        path=request.url.path,
        method=request.method,
        limit=exc.detail
    )
    
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. {exc.detail}",
            "retry_after": getattr(exc, 'retry_after', 60)
        }
    )

# Export the configured limiter
__all__ = ["limiter", "get_auth_rate_limit", "get_general_rate_limit", "rate_limit_exceeded_handler"] 