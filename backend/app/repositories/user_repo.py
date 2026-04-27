"""
User repository — data access for User model.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Find a user by email address."""
        query = self._active_query().where(User.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """Check if an email is already registered."""
        user = await self.get_by_email(email)
        return user is not None
