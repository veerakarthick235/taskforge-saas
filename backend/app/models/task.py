"""
Task model — tenant-scoped entity with status workflow and priority.
"""

import enum
import uuid
from datetime import date
from sqlalchemy import String, Text, ForeignKey, Enum, Date, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, SoftDeleteMixin, TenantMixin


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# Valid status transitions
VALID_TRANSITIONS = {
    TaskStatus.TODO: [TaskStatus.IN_PROGRESS],
    TaskStatus.IN_PROGRESS: [TaskStatus.IN_REVIEW, TaskStatus.TODO],
    TaskStatus.IN_REVIEW: [TaskStatus.DONE, TaskStatus.IN_PROGRESS],
    TaskStatus.DONE: [TaskStatus.TODO],  # Allow reopen
}


class Task(Base, TimestampMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status", create_constraint=True),
        default=TaskStatus.TODO,
        nullable=False,
    )
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority, name="task_priority", create_constraint=True),
        default=TaskPriority.MEDIUM,
        nullable=False,
    )
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    position: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Relationships
    assignee = relationship("User", foreign_keys=[assignee_id], lazy="selectin")
    creator = relationship("User", foreign_keys=[created_by], lazy="selectin")
    organization = relationship("Organization", back_populates="tasks", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Task {self.title[:30]}>"
