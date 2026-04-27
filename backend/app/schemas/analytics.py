"""
Pydantic schemas for analytics endpoints.
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class TaskStatsOverview(BaseModel):
    total_tasks: int
    todo_count: int
    in_progress_count: int
    in_review_count: int
    done_count: int
    overdue_count: int
    total_members: int


class UserPerformance(BaseModel):
    user_id: str
    full_name: str
    email: str
    tasks_assigned: int
    tasks_completed: int
    completion_rate: float


class ActivityEntry(BaseModel):
    id: str
    user_id: str
    user_name: str
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    changes: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True
