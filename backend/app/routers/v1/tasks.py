"""
Tasks router — CRUD, status transitions, assignment.
"""

import uuid
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    get_db,
    get_current_user,
    get_membership,
    require_role,
)
from app.models.user import User
from app.models.membership import Membership, MemberRole
from app.services.task_service import TaskService
from app.schemas.task import (
    CreateTaskRequest,
    UpdateTaskRequest,
    UpdateTaskStatusRequest,
    AssignTaskRequest,
    TaskFilterParams,
)

router = APIRouter(
    prefix="/organizations/{org_id}/tasks",
    tags=["Tasks"],
)


@router.post("/", status_code=201)
async def create_task(
    org_id: uuid.UUID,
    data: CreateTaskRequest,
    membership: Membership = Depends(get_membership),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new task in the organization."""
    service = TaskService(db)
    return await service.create_task(org_id, data, current_user)


@router.get("/")
async def list_tasks(
    org_id: uuid.UUID,
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assignee_id: Optional[str] = Query(None),
    due_before: Optional[date] = Query(None),
    due_after: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    membership: Membership = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
):
    """List tasks with pagination and filtering."""
    filters = TaskFilterParams(
        status=status,
        priority=priority,
        assignee_id=assignee_id,
        due_before=due_before,
        due_after=due_after,
        search=search,
        page=page,
        page_size=page_size,
    )
    service = TaskService(db)
    return await service.get_tasks(org_id, filters)


@router.get("/{task_id}")
async def get_task(
    org_id: uuid.UUID,
    task_id: uuid.UUID,
    membership: Membership = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific task by ID."""
    service = TaskService(db)
    return await service.get_task(org_id, task_id)


@router.patch("/{task_id}")
async def update_task(
    org_id: uuid.UUID,
    task_id: uuid.UUID,
    data: UpdateTaskRequest,
    membership: Membership = Depends(get_membership),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update task fields."""
    service = TaskService(db)
    return await service.update_task(org_id, task_id, data, current_user)


@router.patch("/{task_id}/status")
async def update_task_status(
    org_id: uuid.UUID,
    task_id: uuid.UUID,
    data: UpdateTaskStatusRequest,
    membership: Membership = Depends(get_membership),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update task status with workflow validation."""
    service = TaskService(db)
    return await service.update_task_status(org_id, task_id, data, current_user)


@router.patch("/{task_id}/assign")
async def assign_task(
    org_id: uuid.UUID,
    task_id: uuid.UUID,
    data: AssignTaskRequest,
    membership: Membership = Depends(get_membership),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Assign or unassign a task."""
    service = TaskService(db)
    return await service.assign_task(org_id, task_id, data.assignee_id, current_user)


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    org_id: uuid.UUID,
    task_id: uuid.UUID,
    membership: Membership = Depends(require_role(MemberRole.ADMIN)),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a task. Requires admin+."""
    service = TaskService(db)
    await service.delete_task(org_id, task_id, current_user)
