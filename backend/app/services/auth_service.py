"""
Authentication service — handles registration, login, and token refresh.
"""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.exceptions import InvalidCredentials, ConflictError, ValidationError
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def register(self, data: RegisterRequest) -> dict:
        """
        Register a new user.
        Returns user data + JWT tokens.
        """
        # Check duplicate email
        if await self.user_repo.email_exists(data.email):
            raise ConflictError("An account with this email already exists.")

        # Create user
        user = User(
            email=data.email,
            full_name=data.full_name,
            password_hash=hash_password(data.password),
        )
        user = await self.user_repo.create(user)
        await self.session.commit()

        # Generate tokens
        access_token = create_access_token(user.id, user.email)
        refresh_token = create_refresh_token(user.id)

        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
            },
            "tokens": TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
            ),
        }

    async def login(self, data: LoginRequest) -> dict:
        """
        Authenticate a user with email + password.
        Returns user data + JWT tokens.
        """
        user = await self.user_repo.get_by_email(data.email)
        if not user:
            raise InvalidCredentials()

        if not verify_password(data.password, user.password_hash):
            raise InvalidCredentials()

        if not user.is_active:
            raise InvalidCredentials("Account is deactivated.")

        access_token = create_access_token(user.id, user.email)
        refresh_token = create_refresh_token(user.id)

        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
            },
            "tokens": TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
            ),
        }

    async def refresh_token(self, refresh_token_str: str) -> TokenResponse:
        """
        Validate refresh token and issue new access token.
        """
        from jose import JWTError

        try:
            payload = decode_token(refresh_token_str)
        except JWTError:
            raise InvalidCredentials("Invalid or expired refresh token.")

        if payload.get("type") != "refresh":
            raise InvalidCredentials("Invalid token type.")

        user_id = payload.get("sub")
        user = await self.user_repo.get_by_id(uuid.UUID(user_id))
        if not user or not user.is_active:
            raise InvalidCredentials("User not found or inactive.")

        access_token = create_access_token(user.id, user.email)
        new_refresh = create_refresh_token(user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh,
        )
