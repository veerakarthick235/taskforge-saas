"""
FastAPI application factory with lifespan, middleware, and exception handlers.

Error Response Contract:
  All errors return JSON in this shape:
  {
    "error": {
      "code": "MACHINE_READABLE_CODE",
      "message": "Human-readable description.",
      "status": 403
    }
  }
"""

from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine
from app.models.base import Base
from app.routers.router import v1_router
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.middleware.logging_middleware import LoggingMiddleware
from app.exceptions import AppException


# ─────────────────── Structured Logging Config ───────────────────

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


# ─────────────────── Lifespan ───────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown."""
    logger.info("starting_application", app=settings.APP_NAME, version=settings.APP_VERSION)

    # Create tables (dev only; use Alembic migrations in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("database_tables_ready")
    yield

    await engine.dispose()
    logger.info("application_shutdown")


# ─────────────────── Error Envelope ───────────────────

def _error_response(status_code: int, code: str, message: str, headers: dict = None) -> JSONResponse:
    """Build a standardized error response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "status": status_code,
            }
        },
        headers=headers,
    )


# ─────────────────── App Factory ───────────────────

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Production-grade multi-tenant SaaS Task Management Platform",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # ── Middleware (last added = first executed) ──

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    app.add_middleware(RateLimiterMiddleware)
    app.add_middleware(LoggingMiddleware)

    # ── Exception Handlers (standardized envelope) ──

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """Handle all custom application exceptions."""
        return _error_response(
            status_code=exc.status_code,
            code=exc.error_code,
            message=exc.detail,
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle FastAPI/Starlette HTTPExceptions (including 404, 405, etc.)."""
        # Map status codes to error codes
        code_map = {
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            422: "VALIDATION_ERROR",
            429: "RATE_LIMIT_EXCEEDED",
        }
        code = code_map.get(exc.status_code, "HTTP_ERROR")
        return _error_response(
            status_code=exc.status_code,
            code=code,
            message=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic request validation errors with readable messages."""
        errors = exc.errors()
        # Build a human-readable summary
        messages = []
        for err in errors[:5]:  # cap at 5 to avoid huge payloads
            loc = " → ".join(str(l) for l in err.get("loc", []))
            msg = err.get("msg", "Invalid value")
            messages.append(f"{loc}: {msg}")

        return _error_response(
            status_code=422,
            code="VALIDATION_ERROR",
            message="; ".join(messages) if messages else "Request validation failed.",
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Catch-all for unhandled exceptions. Never leak internals."""
        logger.error(
            "unhandled_exception",
            path=str(request.url.path),
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        return _error_response(
            status_code=500,
            code="INTERNAL_ERROR",
            message="An internal server error occurred. Please try again later.",
        )

    # ── Routes ──

    app.include_router(v1_router)

    @app.get("/health", tags=["Health"])
    async def health_check():
        """Lightweight health probe for load balancers."""
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
        }

    return app


app = create_app()
