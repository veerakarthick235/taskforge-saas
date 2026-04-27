"""
Invite service — handles invitation creation, acceptance, and listing.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invite import Invite, InviteStatus
from app.models.membership import Membership, MemberRole
from app.models.user import User
from app.repositories.invite_repo import InviteRepository
from app.repositories.membership_repo import MembershipRepository
from app.repositories.activity_repo import ActivityRepository
from app.repositories.user_repo import UserRepository
from app.exceptions import (
    ConflictError,
    ResourceNotFound,
    ValidationError,
    PermissionDenied,
)
from app.schemas.invite import CreateInviteRequest


class InviteService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.invite_repo = InviteRepository(session)
        self.membership_repo = MembershipRepository(session)
        self.activity_repo = ActivityRepository(session)
        self.user_repo = UserRepository(session)

    async def create_invite(
        self, org_id: uuid.UUID, data: CreateInviteRequest, inviter: User
    ) -> dict:
        """Create a new invite. Checks for existing membership and pending invites."""

        # Check if user is already a member
        existing_user = await self.user_repo.get_by_email(data.email)
        if existing_user:
            is_member = await self.membership_repo.is_member(existing_user.id, org_id)
            if is_member:
                raise ConflictError("This user is already a member of the organization.")

        # Check for existing pending invite
        existing_invite = await self.invite_repo.get_pending_by_email_and_org(
            data.email, org_id
        )
        if existing_invite:
            raise ConflictError("A pending invite already exists for this email.")

        invite = Invite(
            org_id=org_id,
            email=data.email,
            role=data.role,
            invited_by=inviter.id,
        )
        invite = await self.invite_repo.create(invite)

        await self.activity_repo.log_activity(
            org_id=org_id,
            user_id=inviter.id,
            action="invited",
            entity_type="invite",
            entity_id=invite.id,
            changes={"email": data.email, "role": data.role},
        )

        await self.session.commit()

        return {
            "id": str(invite.id),
            "email": invite.email,
            "role": invite.role,
            "status": invite.status.value,
            "invited_by": str(invite.invited_by),
            "inviter_name": inviter.full_name,
            "expires_at": invite.expires_at,
            "created_at": invite.created_at,
            "org_id": str(invite.org_id),
            "token": invite.token,  # Return token so client can share the link
        }

    async def accept_invite(self, token: str, user: User) -> dict:
        """Accept an invite and create membership."""
        invite = await self.invite_repo.get_by_token(token)
        if not invite:
            raise ResourceNotFound("Invite", "Invalid invite token.")

        if invite.status != InviteStatus.PENDING:
            raise ValidationError("This invite has already been used or expired.")

        if invite.is_expired:
            invite.status = InviteStatus.EXPIRED
            await self.session.commit()
            raise ValidationError("This invite has expired.")

        if invite.email != user.email:
            raise PermissionDenied("This invite was sent to a different email address.")

        # Check if already a member
        if await self.membership_repo.is_member(user.id, invite.org_id):
            raise ConflictError("You are already a member of this organization.")

        # Create membership
        membership = Membership(
            user_id=user.id,
            org_id=invite.org_id,
            role=MemberRole(invite.role),
        )
        await self.membership_repo.create(membership)

        # Mark invite as accepted
        invite.status = InviteStatus.ACCEPTED
        await self.session.commit()

        await self.activity_repo.log_activity(
            org_id=invite.org_id,
            user_id=user.id,
            action="accepted_invite",
            entity_type="invite",
            entity_id=invite.id,
        )
        await self.session.commit()

        return {
            "message": "Invite accepted successfully.",
            "org_id": str(invite.org_id),
            "role": invite.role,
        }

    async def get_pending_invites(self, org_id: uuid.UUID) -> list:
        """Get all pending invites for an org."""
        invites = await self.invite_repo.get_pending_by_org(org_id)
        return [
            {
                "id": str(inv.id),
                "email": inv.email,
                "role": inv.role,
                "status": inv.status.value,
                "invited_by": str(inv.invited_by),
                "inviter_name": inv.inviter.full_name if inv.inviter else None,
                "expires_at": inv.expires_at,
                "created_at": inv.created_at,
                "org_id": str(inv.org_id),
            }
            for inv in invites
        ]

    async def revoke_invite(
        self, org_id: uuid.UUID, invite_id: uuid.UUID, user: User
    ) -> None:
        """Revoke a pending invite."""
        invite = await self.invite_repo.get_by_id(invite_id)
        if not invite or invite.org_id != org_id:
            raise ResourceNotFound("Invite")

        if invite.status != InviteStatus.PENDING:
            raise ValidationError("Only pending invites can be revoked.")

        invite.status = InviteStatus.EXPIRED

        await self.activity_repo.log_activity(
            org_id=org_id,
            user_id=user.id,
            action="revoked_invite",
            entity_type="invite",
            entity_id=invite.id,
            changes={"email": invite.email},
        )

        await self.session.commit()
