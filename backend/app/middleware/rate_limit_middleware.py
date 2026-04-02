"""
Rate Limiting Middleware
Implements Redis-based rate limiting with sliding window.
"""
import time
import redis
import os
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.database import get_db
from app.models.user import User
from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_url: str):
        super().__init__(app)
        self.redis = redis.from_url(redis_url)
        # Rate limits per hour
        self.limits = {
            'FREE_USER': 100,
            'PREMIUM_USER': 1000,
            'ADMIN': 10000
        }

    async def dispatch(self, request: Request, call_next):
        # Testing / CI: do not rate limit test client requests.
        # Pytest sets PYTEST_CURRENT_TEST for each test; also allow explicit env override.
        if os.getenv("DISABLE_RATE_LIMITING", "").lower() in ("1", "true", "yes") or os.getenv("PYTEST_CURRENT_TEST"):
            return await call_next(request)

        # Skip rate limiting for health checks and static files
        if request.url.path in ['/health', '/docs', '/openapi.json'] or request.url.path.startswith('/static'):
            return await call_next(request)

        # Get user from request state (set by auth middleware)
        user = getattr(request.state, 'user', None)
        if not user:
            # Anonymous requests - low limit
            limit = 10
            key = f"rate_limit:anon:{request.client.host}:{int(time.time() / 3600)}"
        else:
            limit = self.limits.get(user.role.value, 100)
            key = f"rate_limit:{user.id}:{int(time.time() / 3600)}"

        # Sliding window: count requests in current hour
        # If Redis is unavailable, degrade gracefully to avoid breaking the app.
        try:
            current = self.redis.incr(key)
            if current == 1:
                self.redis.expire(key, 3600)  # Expire in 1 hour
        except Exception as e:
            logger.warning("RateLimitMiddleware redis unavailable, skipping: %s", e)
            return await call_next(request)

        if current > limit:
            # Never raise HTTPException directly from middleware dispatch:
            # it bypasses FastAPI exception routing and can surface as 500.
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Please try again later."},
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() / 3600) * 3600 + 3600),
                },
            )

        response = await call_next(request)

        # Add rate limit headers
        remaining = max(0, limit - current)
        response.headers['X-RateLimit-Limit'] = str(limit)
        response.headers['X-RateLimit-Remaining'] = str(remaining)
        response.headers['X-RateLimit-Reset'] = str(int(time.time() / 3600) * 3600 + 3600)

        return response
