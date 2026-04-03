"""X-Request-ID для трассировки запросов и JSON-логов (structlog, если есть)."""
from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware

try:
    import structlog

    _has_structlog = True
except ImportError:
    structlog = None  # type: ignore
    _has_structlog = False


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        if _has_structlog:
            structlog.contextvars.bind_contextvars(request_id=rid)
        try:
            request.state.request_id = rid
            response = await call_next(request)
            response.headers["X-Request-ID"] = rid
            return response
        finally:
            if _has_structlog:
                structlog.contextvars.unbind_contextvars("request_id")
