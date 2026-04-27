"""
Membership repository — data access for Membership model.
"""

import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import Membership, MemberRole
from app.repositories.base import BaseRepository


class MembershipRepository(BaseRepository[Membership]):
    def __init__(self, session: AsyncSession):
        super().__init__(Membership, session)

    async def get_membership(
        self, user_id: uuid.UUID, org_id: uuid.UUID
    ) -> Optional[Membership]:
        """Get a specific membership."""
        query = self._active_query().where(
            Membership.user_id == user_id,
            Membership.org_id == org_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_org_members(self, org_id: uuid.UUID) -> List[Membership]:
        """Get all active members of an organization."""
        query = (
            self._active_query()
            .where(Membership.org_id == org_id)
            .order_by(Membership.joined_at.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def is_member(self, user_id: uuid.UUID, org_id: uuid.UUID) -> bool:
        """Check if a user is a member of an org."""
        membership = await self.get_membership(user_id, org_id)
        return membership is not None

    async def get_owner(self, org_id: uuid.UUID) -> Optional[Membership]:
        """Get the owner membership of an org."""
        query = self._active_query().where(
            Membership.org_id == org_id,
            Membership.role == MemberRole.OWNER,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
