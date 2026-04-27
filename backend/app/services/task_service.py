"""
Task service — handles full task lifecycle with tenant isolation and audit.
"""

import uuid
from typing import Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus, TaskPriority, VALID_TRANSITIONS
from app.models.user import User
from app.repositories.task_repo import TaskRepository
from app.repositories.membership_repo import MembershipRepository
from app.repositories.activity_repo import ActivityRepository
from app.exceptions import ResourceNotFound, ValidationError, PermissionDenied
from app.schemas.task import (
    CreateTaskRequest,
    UpdateTaskRequest,
    UpdateTaskStatusRequest,
    TaskFilterParams,
)


class TaskService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.task_repo = TaskRepository(session)
        self.membership_repo = MembershipRepository(session)
        self.activity_repo = ActivityRepository(session)

    def _task_to_dict(self, task: Task) -> dict:
        """Convert a task ORM model to response dict."""
        return {
            "id": str(task.id),
            "title": task.title,
            "description": task.description,
            "status": task.status.value if isinstance(task.status, TaskStatus) else task.status,
            "priority": task.priority.value if isinstance(task.priority, TaskPriority) else task.priority,
            "assignee_id": str(task.assignee_id) if task.assignee_id else None,
            "assignee_name": task.assignee.full_name if task.assignee else None,
            "created_by": str(task.created_by),
            "creator_name": task.creator.full_name if task.creator else None,
            "due_date": task.due_date,
            "position": task.position,
            "org_id": str(task.org_id),
            "created_at": task.created_at,
            "updated_at": task.updated_at,
        }

    async def create_task(
        self, org_id: uuid.UUID, data: CreateTaskRequest, user: User
    ) -> dict:
        """Create a new task within an org."""
        # Validate assignee membership if provided
        if data.assignee_id:
            assignee_uuid = uuid.UUID(data.assignee_id)
            is_member = await self.membership_repo.is_member(assignee_uuid, org_id)
            if not is_member:
                raise ValidationError("Assignee is not a member of this organization.")

        position = await self.task_repo.get_max_position(org_id)

        task = Task(
            org_id=org_id,
            title=data.title,
            description=data.description,
            priority=TaskPriority(data.priority),
            assignee_id=uuid.UUID(data.assignee_id) if data.assignee_id else None,
            created_by=user.id,
            due_date=data.due_date,
            position=position,
        )
        task = await self.task_repo.create(task)

        # Audit
        await self.activity_repo.log_activity(
            org_id=org_id,
            user_id=user.id,
            action="created",
            entity_type="task",
            entity_id=task.id,
            changes={"title": data.title, "priority": data.priority},
        )

        await self.session.commit()
        # Refresh to load relationships
        await self.session.refresh(task)
        return self._task_to_dict(task)

    async def get_tasks(
        self, org_id: uuid.UUID, filters: TaskFilterParams
    ) -> dict:
        """Get paginated, filtered tasks for an org."""
        offset = (filters.page - 1) * filters.page_size
        limit = min(filters.page_size, 100)

        tasks, total = await self.task_repo.get_tasks_paginated(
            org_id=org_id,
            offset=offset,
            limit=limit,
            status=filters.status,
            priority=filters.priority,
            assignee_id=uuid.UUID(filters.assignee_id) if filters.assignee_id else None,
            due_before=filters.due_before,
            due_after=filters.due_after,
            search=filters.search,
        )

        total_pages = max(1, (total + limit - 1) // limit)

        return {
            "items": [self._task_to_dict(t) for t in tasks],
            "total": total,
            "page": filters.page,
            "page_size": limit,
            "total_pages": total_pages,
        }

    async def get_task(self, org_id: uuid.UUID, task_id: uuid.UUID) -> dict:
        """Get a single task by ID within an org."""
        task = await self.task_repo.get_by_org(org_id, task_id)
        if not task:
            raise ResourceNotFound("Task")
        return self._task_to_dict(task)

    async def update_task(
        self, org_id: uuid.UUID, task_id: uuid.UUID, data: UpdateTaskRequest, user: User
    ) -> dict:
        """Update task fields."""
        task = await self.task_repo.get_by_org(org_id, task_id)
        if not task:
            raise ResourceNotFound("Task")

        changes = {}

        if data.title is not None:
            changes["title"] = {"old": task.title, "new": data.title}
            task.title = data.title
        if data.description is not None:
            task.description = data.description
            changes["description"] = "updated"
        if data.priority is not None:
            changes["priority"] = {"old": task.priority.value, "new": data.priority}
            task.priority = TaskPriority(data.priority)
        if data.assignee_id is not None:
            # Validate membership
            assignee_uuid = uuid.UUID(data.assignee_id)
            if not await self.membership_repo.is_member(assignee_uuid, org_id):
                raise ValidationError("Assignee is not a member of this organization.")
            task.assignee_id = assignee_uuid
            changes["assignee_id"] = data.assignee_id
        if data.due_date is not None:
            task.due_date = data.due_date
            changes["due_date"] = str(data.due_date)

        await self.task_repo.update(task)

        if changes:
            await self.activity_repo.log_activity(
                org_id=org_id,
                user_id=user.id,
                action="updated",
                entity_type="task",
                entity_id=task.id,
                changes=changes,
            )

        await self.session.commit()
        await self.session.refresh(task)
        return self._task_to_dict(task)

    async def update_task_status(
        self, org_id: uuid.UUID, task_id: uuid.UUID, data: UpdateTaskStatusRequest, user: User
    ) -> dict:
        """Update task status with workflow validation."""
        task = await self.task_repo.get_by_org(org_id, task_id)
        if not task:
            raise ResourceNotFound("Task")

        new_status = TaskStatus(data.status)
        current_status = task.status

        # Validate transition
        allowed = VALID_TRANSITIONS.get(current_status, [])
        if new_status not in allowed:
            raise ValidationError(
                f"Cannot transition from '{current_status.value}' to '{new_status.value}'. "
                f"Allowed: {[s.value for s in allowed]}"
            )

        old_status = current_status.value
        task.status = new_status
        await self.task_repo.update(task)

        await self.activity_repo.log_activity(
            org_id=org_id,
            user_id=user.id,
            action="status_changed",
            entity_type="task",
            entity_id=task.id,
            changes={"old_status": old_status, "new_status": new_status.value},
        )

        await self.session.commit()
        await self.session.refresh(task)
        return self._task_to_dict(task)

    async def assign_task(
        self, org_id: uuid.UUID, task_id: uuid.UUID, assignee_id: Optional[str], user: User
    ) -> dict:
        """Assign or unassign a task."""
        task = await self.task_repo.get_by_org(org_id, task_id)
        if not task:
            raise ResourceNotFound("Task")

        if assignee_id:
            assignee_uuid = uuid.UUID(assignee_id)
            if not await self.membership_repo.is_member(assignee_uuid, org_id):
                raise ValidationError("Assignee is not a member of this organization.")
            task.assignee_id = assignee_uuid
        else:
            task.assignee_id = None

        await self.task_repo.update(task)

        await self.activity_repo.log_activity(
            org_id=org_id,
            user_id=user.id,
            action="assigned",
            entity_type="task",
            entity_id=task.id,
            changes={"assignee_id": assignee_id},
        )

        await self.session.commit()
        await self.session.refresh(task)
        return self._task_to_dict(task)

    async def delete_task(
        self, org_id: uuid.UUID, task_id: uuid.UUID, user: User
    ) -> None:
        """Soft delete a task (admin+)."""
        task = await self.task_repo.get_by_org(org_id, task_id)
        if not task:
            raise ResourceNotFound("Task")

        await self.task_repo.soft_delete(task)

        await self.activity_repo.log_activity(
            org_id=org_id,
            user_id=user.id,
            action="deleted",
            entity_type="task",
            entity_id=task.id,
            changes={"title": task.title},
        )

        await self.session.commit()
