"""
Auth router — registration, login, token refresh, and user profile.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.auth_service import AuthService
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    service = AuthService(db)
    result = await service.register(data)
    return result


@router.post("/login")
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate with email and password."""
    service = AuthService(db)
    result = await service.login(data)
    return result


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh an expired access token."""
    service = AuthService(db)
    return await service.refresh_token(data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
    )
