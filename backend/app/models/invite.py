"""
Invite model — token-based organization invite system.
"""

import uuid
import enum
import secrets
from datetime import datetime, timezone, timedelta
from sqlalchemy import String, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TenantMixin


class InviteStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"


class Invite(Base, TenantMixin):
    __tablename__ = "invites"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(50),
        default="member",
        nullable=False,
    )
    token: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        default=lambda: secrets.token_urlsafe(32),
        index=True,
    )
    status: Mapped[InviteStatus] = mapped_column(
        Enum(InviteStatus, name="invite_status", create_constraint=True),
        default=InviteStatus.PENDING,
        nullable=False,
    )
    invited_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc) + timedelta(days=7),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    inviter = relationship("User", foreign_keys=[invited_by], lazy="selectin")

    def __repr__(self) -> str:
        return f"<Invite {self.email} -> org={self.org_id}>"

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at
