"""
Analytics router — task stats, user performance, activity feed.
"""

import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    get_db,
    get_membership,
    require_role,
)
from app.models.membership import Membership, MemberRole
from app.services.analytics_service import AnalyticsService

router = APIRouter(
    prefix="/organizations/{org_id}/analytics",
    tags=["Analytics"],
)


@router.get("/overview")
async def get_overview(
    org_id: uuid.UUID,
    membership: Membership = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
):
    """Get task statistics overview for the organization."""
    service = AnalyticsService(db)
    return await service.get_overview(org_id)


@router.get("/user-performance")
async def get_user_performance(
    org_id: uuid.UUID,
    membership: Membership = Depends(require_role(MemberRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Get task completion stats per user. Requires admin+."""
    service = AnalyticsService(db)
    return await service.get_user_performance(org_id)


@router.get("/activity-feed")
async def get_activity_feed(
    org_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    membership: Membership = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
):
    """Get recent activity feed for the organization."""
    service = AnalyticsService(db)
    return await service.get_activity_feed(org_id, page, page_size)
