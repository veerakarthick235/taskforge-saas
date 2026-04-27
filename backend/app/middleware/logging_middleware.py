"""
Structured logging middleware with request tracing.

Every request gets:
  - A unique request_id (full UUID for distributed tracing)
  - Tenant context from X-Org-ID header
  - Authorization user_id (extracted from JWT 'sub' claim, best-effort)
  - Latency in milliseconds
  - Response status code
  - Client IP

Format: JSON (machine-parseable for log aggregation systems like ELK/Datadog)
"""

import time
import uuid
import structlog
from jose import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import settings

logger = structlog.get_logger()


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every HTTP request with structured fields.
    Attaches X-Request-ID response header for client-side correlation.
    """

    async def dispatch(self, request: Request, call_next):
        # Full UUID for distributed tracing (not truncated)
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Extract tenant context (best effort, pre-auth)
        tenant_id = request.headers.get("X-Org-ID", "-")

        # Extract user_id from JWT (best effort, no validation)
        user_id = "-"
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                token = auth_header[7:]
                payload = jwt.get_unverified_claims(token)
                user_id = payload.get("sub", "-")
            except Exception:
                pass

        # Attach to request state for downstream services
        request.state.request_id = request_id
        request.state.tenant_id = tenant_id
        request.state.user_id = user_id

        try:
            response = await call_next(request)
            latency_ms = round((time.time() - start_time) * 1000, 2)

            # Log level based on status code
            log_fn = logger.info if response.status_code < 400 else (
                logger.warning if response.status_code < 500 else logger.error
            )
            log_fn(
                "http_request",
                request_id=request_id,
                method=request.method,
                path=str(request.url.path),
                query=str(request.url.query) if request.url.query else None,
                status=response.status_code,
                latency_ms=latency_ms,
                tenant_id=tenant_id,
                user_id=user_id,
                client_ip=request.client.host if request.client else "unknown",
                user_agent=request.headers.get("User-Agent", "-")[:100],
            )

            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as exc:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(
                "http_request_exception",
                request_id=request_id,
                method=request.method,
                path=str(request.url.path),
                latency_ms=latency_ms,
                tenant_id=tenant_id,
                user_id=user_id,
                error_type=type(exc).__name__,
                error=str(exc),
                client_ip=request.client.host if request.client else "unknown",
            )
            raise
