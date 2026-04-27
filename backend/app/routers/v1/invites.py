"""
Invites router — create, list, accept, and revoke invites.
"""

import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    get_db,
    get_current_user,
    require_role,
)
from app.models.user import User
from app.models.membership import Membership, MemberRole
from app.services.invite_service import InviteService
from app.schemas.invite import CreateInviteRequest, AcceptInviteRequest

router = APIRouter(tags=["Invites"])


@router.post("/organizations/{org_id}/invites/", status_code=201)
async def create_invite(
    org_id: uuid.UUID,
    data: CreateInviteRequest,
    membership: Membership = Depends(require_role(MemberRole.ADMIN)),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an invite for a new member. Requires admin+."""
    service = InviteService(db)
    return await service.create_invite(org_id, data, current_user)


@router.get("/organizations/{org_id}/invites/")
async def list_invites(
    org_id: uuid.UUID,
    membership: Membership = Depends(require_role(MemberRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """List all pending invites for the org. Requires admin+."""
    service = InviteService(db)
    return await service.get_pending_invites(org_id)


@router.delete("/organizations/{org_id}/invites/{invite_id}", status_code=204)
async def revoke_invite(
    org_id: uuid.UUID,
    invite_id: uuid.UUID,
    membership: Membership = Depends(require_role(MemberRole.ADMIN)),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke a pending invite. Requires admin+."""
    service = InviteService(db)
    await service.revoke_invite(org_id, invite_id, current_user)


@router.post("/invites/accept")
async def accept_invite(
    data: AcceptInviteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Accept an invite using a token."""
    service = InviteService(db)
    return await service.accept_invite(data.token, current_user)
