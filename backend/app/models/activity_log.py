"""
ActivityLog model — audit trail for tenant actions.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TenantMixin


class ActivityLog(Base, TenantMixin):
    __tablename__ = "activity_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    entity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    changes: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    user = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<ActivityLog {self.action} on {self.entity_type}>"
