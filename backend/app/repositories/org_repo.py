"""
Organization repository — data access for Organization model.
"""

import uuid
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.membership import Membership
from app.repositories.base import BaseRepository


class OrgRepository(BaseRepository[Organization]):
    def __init__(self, session: AsyncSession):
        super().__init__(Organization, session)

    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        """Find org by slug."""
        query = self._active_query().where(Organization.slug == slug)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str) -> bool:
        """Check if a slug is taken."""
        org = await self.get_by_slug(slug)
        return org is not None

    async def get_user_organizations(self, user_id: uuid.UUID) -> List[Organization]:
        """Get all organizations a user belongs to."""
        query = (
            select(Organization)
            .join(Membership, Membership.org_id == Organization.id)
            .where(
                Membership.user_id == user_id,
                Membership.deleted_at == None,
                Organization.deleted_at == None,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_member_count(self, org_id: uuid.UUID) -> int:
        """Count active members of an organization."""
        query = select(func.count(Membership.id)).where(
            Membership.org_id == org_id,
            Membership.deleted_at == None,
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
