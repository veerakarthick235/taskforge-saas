"""
Organizations router — CRUD, members, and role management.
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    get_db,
    get_current_user,
    get_membership,
    get_org_id,
    require_role,
)
from app.models.user import User
from app.models.membership import Membership, MemberRole
from app.services.org_service import OrgService
from app.schemas.organization import (
    CreateOrgRequest,
    UpdateOrgRequest,
    OrgResponse,
    MemberResponse,
    UpdateMemberRoleRequest,
)

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.post("/", status_code=201)
async def create_organization(
    data: CreateOrgRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new organization. The creator becomes the owner."""
    service = OrgService(db)
    return await service.create_organization(data, current_user)


@router.get("/")
async def list_organizations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all organizations the current user belongs to."""
    service = OrgService(db)
    return await service.get_user_organizations(current_user)


@router.get("/{org_id}")
async def get_organization(
    org_id: uuid.UUID,
    membership: Membership = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
):
    """Get organization details. Requires membership."""
    service = OrgService(db)
    return await service.get_organization(org_id)


@router.patch("/{org_id}")
async def update_organization(
    org_id: uuid.UUID,
    data: UpdateOrgRequest,
    membership: Membership = Depends(require_role(MemberRole.ADMIN)),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update organization details. Requires admin+ role."""
    service = OrgService(db)
    return await service.update_organization(org_id, data, current_user)


@router.get("/{org_id}/members")
async def list_members(
    org_id: uuid.UUID,
    membership: Membership = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
):
    """List all members of the organization."""
    service = OrgService(db)
    return await service.get_members(org_id)


@router.delete("/{org_id}/members/{user_id}", status_code=204)
async def remove_member(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    membership: Membership = Depends(require_role(MemberRole.ADMIN)),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a member from the organization. Requires admin+. Cannot remove owner."""
    service = OrgService(db)
    await service.remove_member(org_id, user_id, current_user)


@router.patch("/{org_id}/members/{user_id}/role")
async def update_member_role(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    data: UpdateMemberRoleRequest,
    membership: Membership = Depends(require_role(MemberRole.OWNER)),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change a member's role. Owner only."""
    service = OrgService(db)
    return await service.update_member_role(org_id, user_id, data.role, current_user)
