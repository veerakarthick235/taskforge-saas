"""
Membership model — links users to organizations with roles.
"""

import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, UniqueConstraint, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin


class MemberRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


# Role hierarchy for permission checks
ROLE_HIERARCHY = {
    MemberRole.MEMBER: 0,
    MemberRole.ADMIN: 1,
    MemberRole.OWNER: 2,
}


def has_permission(user_role: MemberRole, required_role: MemberRole) -> bool:
    """Check if user_role has at least the required_role level."""
    return ROLE_HIERARCHY.get(user_role, -1) >= ROLE_HIERARCHY.get(required_role, 99)


class Membership(Base, SoftDeleteMixin):
    __tablename__ = "memberships"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[MemberRole] = mapped_column(
        Enum(MemberRole, name="member_role", create_constraint=True),
        default=MemberRole.MEMBER,
        nullable=False,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="memberships", lazy="selectin")
    organization = relationship("Organization", back_populates="memberships", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("user_id", "org_id", name="uq_user_org_membership"),
    )

    def __repr__(self) -> str:
        return f"<Membership user={self.user_id} org={self.org_id} role={self.role}>"
