"""
V1 API router — aggregates all v1 route modules.
"""

from fastapi import APIRouter

from app.routers.v1.auth import router as auth_router
from app.routers.v1.organizations import router as orgs_router
from app.routers.v1.tasks import router as tasks_router
from app.routers.v1.invites import router as invites_router
from app.routers.v1.analytics import router as analytics_router

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(auth_router)
v1_router.include_router(orgs_router)
v1_router.include_router(tasks_router)
v1_router.include_router(invites_router)
v1_router.include_router(analytics_router)
