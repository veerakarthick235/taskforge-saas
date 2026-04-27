"""
Custom exception classes mapped to HTTP status codes.

All exceptions produce a standardized JSON error envelope:
{
  "error": {
    "code": "TENANT_ACCESS_DENIED",
    "message": "Access denied: you are not a member of this organization.",
    "status": 403
  }
}
"""

from fastapi import HTTPException, status


class AppException(HTTPException):
    """
    Base application exception with a machine-readable error code.
    All custom exceptions extend this.
    """
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, status_code: int, detail: str, error_code: str = None, headers: dict = None):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code or self.__class__.error_code


class TenantAccessDenied(AppException):
    """Raised when a user tries to access another tenant's data."""
    error_code = "TENANT_ACCESS_DENIED"

    def __init__(self, detail: str = "Access denied: you are not a member of this organization."):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ResourceNotFound(AppException):
    """Raised when a requested resource does not exist."""
    error_code = "RESOURCE_NOT_FOUND"

    def __init__(self, resource: str = "Resource", detail: str | None = None):
        msg = detail or f"{resource} not found."
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=msg)


class PermissionDenied(AppException):
    """Raised when a user lacks the required role/permission."""
    error_code = "PERMISSION_DENIED"

    def __init__(self, detail: str = "You do not have permission to perform this action."):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class InvalidCredentials(AppException):
    """Raised on invalid login credentials or expired/malformed tokens."""
    error_code = "INVALID_CREDENTIALS"

    def __init__(self, detail: str = "Invalid email or password."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class TokenExpired(AppException):
    """Raised when a JWT token has expired."""
    error_code = "TOKEN_EXPIRED"

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please refresh your session.",
            headers={"WWW-Authenticate": "Bearer"},
        )


class ValidationError(AppException):
    """Raised on business logic validation failures."""
    error_code = "VALIDATION_ERROR"

    def __init__(self, detail: str = "Validation error."):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class ConflictError(AppException):
    """Raised on duplicate resource creation."""
    error_code = "CONFLICT"

    def __init__(self, detail: str = "Resource already exists."):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class RateLimitExceeded(AppException):
    """Raised when rate limit is exceeded."""
    error_code = "RATE_LIMIT_EXCEEDED"

    def __init__(self, retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )
