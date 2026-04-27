"""
In-memory sliding window rate limiter middleware.
"""

import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory sliding window rate limiter per IP.
    In production, replace with Redis-backed solution.
    """

    def __init__(self, app, max_requests: int = None, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests or settings.RATE_LIMIT_PER_MINUTE
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ("/health", "/docs", "/openapi.json"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old entries and add current
        self._requests[client_ip] = [
            ts for ts in self._requests[client_ip] if ts > window_start
        ]

        if len(self._requests[client_ip]) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."},
                headers={"Retry-After": str(self.window_seconds)},
            )

        self._requests[client_ip].append(now)
        return await call_next(request)
