"""
Activity repository — data access for ActivityLog model.
"""

import uuid
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog
from app.repositories.base import BaseRepository


class ActivityRepository(BaseRepository[ActivityLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(ActivityLog, session)

    async def get_org_activity(
        self,
        org_id: uuid.UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> List[ActivityLog]:
        """Get recent activity for an organization."""
        query = (
            select(ActivityLog)
            .where(ActivityLog.org_id == org_id)
            .order_by(ActivityLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def log_activity(
        self,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID = None,
        changes: dict = None,
    ) -> ActivityLog:
        """Create an audit log entry."""
        log = ActivityLog(
            org_id=org_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            changes=changes,
        )
        return await self.create(log)
