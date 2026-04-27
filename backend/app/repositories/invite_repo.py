"""
Invite repository — data access for Invite model.
"""

import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invite import Invite, InviteStatus
from app.repositories.base import BaseRepository


class InviteRepository(BaseRepository[Invite]):
    def __init__(self, session: AsyncSession):
        super().__init__(Invite, session)

    async def get_by_token(self, token: str) -> Optional[Invite]:
        """Find an invite by its token."""
        query = select(Invite).where(Invite.token == token)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_pending_by_org(self, org_id: uuid.UUID) -> List[Invite]:
        """Get all pending invites for an org."""
        query = (
            select(Invite)
            .where(
                Invite.org_id == org_id,
                Invite.status == InviteStatus.PENDING,
            )
            .order_by(Invite.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_by_email_and_org(
        self, email: str, org_id: uuid.UUID
    ) -> Optional[Invite]:
        """Check if there's already a pending invite for this email+org."""
        query = select(Invite).where(
            Invite.email == email,
            Invite.org_id == org_id,
            Invite.status == InviteStatus.PENDING,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
