"""
Task repository — data access for Task model with filtering and pagination.
"""

import uuid
from typing import Optional, List, Tuple
from datetime import date
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus, TaskPriority
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    def __init__(self, session: AsyncSession):
        super().__init__(Task, session)

    async def get_tasks_paginated(
        self,
        org_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee_id: Optional[uuid.UUID] = None,
        due_before: Optional[date] = None,
        due_after: Optional[date] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Task], int]:
        """
        Get tasks with filtering and pagination.
        Returns (tasks, total_count).
        """
        base_query = self._active_query().where(Task.org_id == org_id)

        # Apply filters
        if status:
            base_query = base_query.where(Task.status == status)
        if priority:
            base_query = base_query.where(Task.priority == priority)
        if assignee_id:
            base_query = base_query.where(Task.assignee_id == assignee_id)
        if due_before:
            base_query = base_query.where(Task.due_date <= due_before)
        if due_after:
            base_query = base_query.where(Task.due_date >= due_after)
        if search:
            base_query = base_query.where(
                Task.title.ilike(f"%{search}%")
            )

        # Count query
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await self.session.execute(count_query)).scalar() or 0

        # Data query with ordering and pagination
        data_query = (
            base_query
            .order_by(Task.position.asc(), Task.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(data_query)
        tasks = list(result.scalars().all())

        return tasks, total

    async def get_by_org(self, org_id: uuid.UUID, task_id: uuid.UUID) -> Optional[Task]:
        """Get a specific task within an org (tenant-safe)."""
        query = self._active_query().where(
            Task.id == task_id,
            Task.org_id == org_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_max_position(self, org_id: uuid.UUID) -> int:
        """Get the highest position value for tasks in an org."""
        query = select(func.max(Task.position)).where(
            Task.org_id == org_id,
            Task.deleted_at == None,
        )
        result = await self.session.execute(query)
        return (result.scalar() or 0) + 1

    async def count_by_status(self, org_id: uuid.UUID) -> dict:
        """Count tasks grouped by status for an org."""
        query = (
            select(Task.status, func.count(Task.id))
            .where(Task.org_id == org_id, Task.deleted_at == None)
            .group_by(Task.status)
        )
        result = await self.session.execute(query)
        return {row[0]: row[1] for row in result.all()}

    async def count_overdue(self, org_id: uuid.UUID) -> int:
        """Count overdue tasks (past due_date, not done)."""
        from datetime import date as date_cls
        query = select(func.count(Task.id)).where(
            Task.org_id == org_id,
            Task.deleted_at == None,
            Task.due_date < date_cls.today(),
            Task.status != TaskStatus.DONE,
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_user_task_stats(self, org_id: uuid.UUID) -> List[dict]:
        """Get task counts per user (assigned and completed)."""
        from app.models.user import User
        from app.models.membership import Membership

        # Get all members and their task stats
        query = (
            select(
                User.id,
                User.full_name,
                User.email,
                func.count(Task.id).label("tasks_assigned"),
                func.sum(
                    func.cast(Task.status == TaskStatus.DONE, type_=func.count.type)
                ).label("tasks_completed"),
            )
            .join(Membership, Membership.user_id == User.id)
            .outerjoin(
                Task,
                and_(
                    Task.assignee_id == User.id,
                    Task.org_id == org_id,
                    Task.deleted_at == None,
                ),
            )
            .where(
                Membership.org_id == org_id,
                Membership.deleted_at == None,
            )
            .group_by(User.id, User.full_name, User.email)
        )
        result = await self.session.execute(query)
        return [
            {
                "user_id": str(row[0]),
                "full_name": row[1],
                "email": row[2],
                "tasks_assigned": row[3] or 0,
                "tasks_completed": row[4] or 0,
            }
            for row in result.all()
        ]
