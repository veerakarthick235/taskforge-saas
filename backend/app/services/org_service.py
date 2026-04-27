"""
Organization service — handles org creation, updates, and member management.
"""

import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.membership import Membership, MemberRole
from app.models.user import User
from app.repositories.org_repo import OrgRepository
from app.repositories.membership_repo import MembershipRepository
from app.repositories.activity_repo import ActivityRepository
from app.exceptions import (
    ConflictError,
    ResourceNotFound,
    PermissionDenied,
    ValidationError,
)
from app.schemas.organization import CreateOrgRequest, UpdateOrgRequest


class OrgService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.org_repo = OrgRepository(session)
        self.membership_repo = MembershipRepository(session)
        self.activity_repo = ActivityRepository(session)

    async def create_organization(
        self, data: CreateOrgRequest, creator: User
    ) -> dict:
        """
        Create a new organization and set the creator as owner.
        """
        # Check slug uniqueness
        if await self.org_repo.slug_exists(data.slug):
            raise ConflictError(f"Organization slug '{data.slug}' is already taken.")

        # Create org
        org = Organization(
            name=data.name,
            slug=data.slug,
            created_by=creator.id,
        )
        org = await self.org_repo.create(org)

        # Create owner membership
        membership = Membership(
            user_id=creator.id,
            org_id=org.id,
            role=MemberRole.OWNER,
        )
        await self.membership_repo.create(membership)

        # Audit log
        await self.activity_repo.log_activity(
            org_id=org.id,
            user_id=creator.id,
            action="created",
            entity_type="organization",
            entity_id=org.id,
            changes={"name": data.name, "slug": data.slug},
        )

        await self.session.commit()

        return {
            "id": str(org.id),
            "name": org.name,
            "slug": org.slug,
            "created_by": str(org.created_by),
            "created_at": org.created_at,
            "member_count": 1,
        }

    async def get_user_organizations(self, user: User) -> List[dict]:
        """Get all orgs the user belongs to."""
        orgs = await self.org_repo.get_user_organizations(user.id)
        result = []
        for org in orgs:
            count = await self.org_repo.get_member_count(org.id)
            result.append({
                "id": str(org.id),
                "name": org.name,
                "slug": org.slug,
                "created_by": str(org.created_by),
                "created_at": org.created_at,
                "member_count": count,
            })
        return result

    async def get_organization(self, org_id: uuid.UUID) -> dict:
        """Get organization details."""
        org = await self.org_repo.get_by_id(org_id)
        if not org:
            raise ResourceNotFound("Organization")
        count = await self.org_repo.get_member_count(org.id)
        return {
            "id": str(org.id),
            "name": org.name,
            "slug": org.slug,
            "created_by": str(org.created_by),
            "created_at": org.created_at,
            "member_count": count,
        }

    async def update_organization(
        self, org_id: uuid.UUID, data: UpdateOrgRequest, user: User
    ) -> dict:
        """Update org details (admin+)."""
        org = await self.org_repo.get_by_id(org_id)
        if not org:
            raise ResourceNotFound("Organization")

        if data.name is not None:
            org.name = data.name

        await self.org_repo.update(org)

        await self.activity_repo.log_activity(
            org_id=org.id,
            user_id=user.id,
            action="updated",
            entity_type="organization",
            entity_id=org.id,
            changes=data.model_dump(exclude_none=True),
        )

        await self.session.commit()

        return await self.get_organization(org_id)

    async def get_members(self, org_id: uuid.UUID) -> List[dict]:
        """Get all members of an org."""
        memberships = await self.membership_repo.get_org_members(org_id)
        return [
            {
                "id": str(m.id),
                "user_id": str(m.user_id),
                "email": m.user.email,
                "full_name": m.user.full_name,
                "role": m.role.value,
                "joined_at": m.joined_at,
            }
            for m in memberships
        ]

    async def remove_member(
        self, org_id: uuid.UUID, target_user_id: uuid.UUID, acting_user: User
    ) -> None:
        """Remove a member from org (admin+). Cannot remove owner."""
        membership = await self.membership_repo.get_membership(target_user_id, org_id)
        if not membership:
            raise ResourceNotFound("Member")

        if membership.role == MemberRole.OWNER:
            raise PermissionDenied("Cannot remove the organization owner.")

        await self.membership_repo.soft_delete(membership)

        await self.activity_repo.log_activity(
            org_id=org_id,
            user_id=acting_user.id,
            action="removed_member",
            entity_type="membership",
            entity_id=membership.id,
            changes={"removed_user_id": str(target_user_id)},
        )

        await self.session.commit()

    async def update_member_role(
        self,
        org_id: uuid.UUID,
        target_user_id: uuid.UUID,
        new_role: str,
        acting_user: User,
    ) -> dict:
        """Change a member's role (owner only). Cannot change owner role."""
        membership = await self.membership_repo.get_membership(target_user_id, org_id)
        if not membership:
            raise ResourceNotFound("Member")

        if membership.role == MemberRole.OWNER:
            raise PermissionDenied("Cannot change the owner's role.")

        membership.role = MemberRole(new_role)
        await self.membership_repo.update(membership)

        await self.activity_repo.log_activity(
            org_id=org_id,
            user_id=acting_user.id,
            action="changed_role",
            entity_type="membership",
            entity_id=membership.id,
            changes={"user_id": str(target_user_id), "new_role": new_role},
        )

        await self.session.commit()

        return {
            "id": str(membership.id),
            "user_id": str(membership.user_id),
            "email": membership.user.email,
            "full_name": membership.user.full_name,
            "role": membership.role.value,
            "joined_at": membership.joined_at,
        }
