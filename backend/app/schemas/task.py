"""
Pydantic schemas for task endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


class CreateTaskRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    priority: str = Field(default="medium", pattern=r"^(low|medium|high|urgent)$")
    assignee_id: Optional[str] = None
    due_date: Optional[date] = None


class UpdateTaskRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    priority: Optional[str] = Field(None, pattern=r"^(low|medium|high|urgent)$")
    assignee_id: Optional[str] = None
    due_date: Optional[date] = None


class UpdateTaskStatusRequest(BaseModel):
    status: str = Field(..., pattern=r"^(todo|in_progress|in_review|done)$")


class AssignTaskRequest(BaseModel):
    assignee_id: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    assignee_id: Optional[str] = None
    assignee_name: Optional[str] = None
    created_by: str
    creator_name: Optional[str] = None
    due_date: Optional[date] = None
    position: int
    org_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskFilterParams(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[str] = None
    due_before: Optional[date] = None
    due_after: Optional[date] = None
    search: Optional[str] = None
    page: int = 1
    page_size: int = 20
