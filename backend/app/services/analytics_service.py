"""
Analytics service — task statistics and activity feed.
"""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.task_repo import TaskRepository
from app.repositories.membership_repo import MembershipRepository
from app.repositories.activity_repo import ActivityRepository
from app.repositories.org_repo import OrgRepository


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.task_repo = TaskRepository(session)
        self.membership_repo = MembershipRepository(session)
        self.activity_repo = ActivityRepository(session)
        self.org_repo = OrgRepository(session)

    async def get_overview(self, org_id: uuid.UUID) -> dict:
        """Get task stats overview for an org."""
        status_counts = await self.task_repo.count_by_status(org_id)
        overdue = await self.task_repo.count_overdue(org_id)
        member_count = await self.org_repo.get_member_count(org_id)

        total = sum(status_counts.values())

        return {
            "total_tasks": total,
            "todo_count": status_counts.get("todo", 0),
            "in_progress_count": status_counts.get("in_progress", 0),
            "in_review_count": status_counts.get("in_review", 0),
            "done_count": status_counts.get("done", 0),
            "overdue_count": overdue,
            "total_members": member_count,
        }

    async def get_user_performance(self, org_id: uuid.UUID) -> list:
        """Get task completion stats per user."""
        stats = await self.task_repo.get_user_task_stats(org_id)
        result = []
        for s in stats:
            assigned = s["tasks_assigned"]
            completed = s["tasks_completed"] or 0
            rate = round(completed / assigned * 100, 1) if assigned > 0 else 0.0
            result.append({
                "user_id": s["user_id"],
                "full_name": s["full_name"],
                "email": s["email"],
                "tasks_assigned": assigned,
                "tasks_completed": completed,
                "completion_rate": rate,
            })
        return result

    async def get_activity_feed(
        self, org_id: uuid.UUID, page: int = 1, page_size: int = 50
    ) -> list:
        """Get recent activity feed for an org."""
        offset = (page - 1) * page_size
        activities = await self.activity_repo.get_org_activity(
            org_id, offset=offset, limit=page_size
        )
        return [
            {
                "id": str(a.id),
                "user_id": str(a.user_id),
                "user_name": a.user.full_name if a.user else "Unknown",
                "action": a.action,
                "entity_type": a.entity_type,
                "entity_id": str(a.entity_id) if a.entity_id else None,
                "changes": a.changes,
                "created_at": a.created_at,
            }
            for a in activities
        ]
