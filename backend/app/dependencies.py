"""
FastAPI dependencies for authentication, tenant context, and RBAC.

Security model:
  1. get_current_user   — validates JWT, resolves User from DB
  2. get_org_id         — extracts X-Org-ID header
  3. get_membership     — proves user is a member of the requested org
  4. require_role()     — enforces minimum role level (Owner > Admin > Member)

Tenant context is injected into the DB session via SET LOCAL app.current_tenant.
This means that even if service code omits an org_id filter, PostgreSQL RLS
will reject cross-tenant rows at the database level.
"""

import uuid
from typing import Optional

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionFactory
from app.exceptions import (
    InvalidCredentials,
    TenantAccessDenied,
    PermissionDenied,
    TokenExpired,
)
from app.models import User, Membership, MemberRole, has_permission
from app.utils.security import decode_token

security_scheme = HTTPBearer()


# ─────────────────── DB Sessions ───────────────────

async def get_db():
    """
    Dependency: Yield a plain async DB session (no tenant scope).
    Used ONLY for auth endpoints where no tenant context exists yet.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def get_tenant_db(
    org_id: uuid.UUID = Depends(lambda x_org_id=Header(None, alias="X-Org-ID"): _parse_org_id(x_org_id)),
) -> AsyncSession:
    """
    Dependency: Yield a tenant-scoped DB session.
    Sets PostgreSQL GUC 'app.current_tenant' via SET LOCAL for RLS.
    """
    async with AsyncSessionFactory() as session:
        try:
            await session.begin()
            await session.execute(
                text("SET LOCAL app.current_tenant = :tenant_id"),
                {"tenant_id": str(org_id)},
            )
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def _parse_org_id(x_org_id: Optional[str]) -> uuid.UUID:
    """Parse and validate X-Org-ID header value."""
    if not x_org_id:
        raise TenantAccessDenied("X-Org-ID header is required.")
    try:
        return uuid.UUID(x_org_id)
    except ValueError:
        raise TenantAccessDenied("Invalid organization ID format.")


# ─────────────────── Auth ───────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency: Extract and validate user from JWT access token.

    Validates:
      - Token signature and expiry (via python-jose)
      - Token type is 'access' (not 'refresh')
      - User exists, is active, and not soft-deleted
    """
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except JWTError:
        raise InvalidCredentials("Invalid or expired token.")

    if payload.get("type") != "access":
        raise InvalidCredentials("Invalid token type. Expected access token.")

    user_id = payload.get("sub")
    if not user_id:
        raise InvalidCredentials("Invalid token payload: missing subject.")

    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise InvalidCredentials("Invalid token payload: malformed user ID.")

    result = await db.execute(
        select(User).where(
            User.id == uid,
            User.is_active == True,
            User.deleted_at == None,
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise InvalidCredentials("User not found or deactivated.")

    return user


# ─────────────────── Tenant Context ───────────────────

async def get_org_id(
    x_org_id: Optional[str] = Header(None, alias="X-Org-ID"),
) -> uuid.UUID:
    """Dependency: Extract and validate organization ID from X-Org-ID header."""
    return _parse_org_id(x_org_id)


async def get_membership(
    org_id: uuid.UUID = Depends(get_org_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Membership:
    """
    Dependency: Verify user is a member of the specified organization.

    This is the PRIMARY tenant gate. If this dependency rejects the request,
    no service code runs, and no DB session with tenant context is created.

    Returns the Membership object (includes role for downstream RBAC checks).
    """
    result = await db.execute(
        select(Membership).where(
            Membership.user_id == current_user.id,
            Membership.org_id == org_id,
            Membership.deleted_at == None,
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise TenantAccessDenied(
            "Access denied: you are not a member of this organization."
        )

    return membership


# ─────────────────── RBAC ───────────────────

def require_role(min_role: MemberRole):
    """
    Dependency factory: Enforce minimum role level.

    Role hierarchy:
      Member (0) < Admin (1) < Owner (2)

    Usage:
      @router.delete("/", dependencies=[Depends(require_role(MemberRole.ADMIN))])
      or
      membership: Membership = Depends(require_role(MemberRole.ADMIN))
    """
    async def role_checker(
        membership: Membership = Depends(get_membership),
    ) -> Membership:
        if not has_permission(membership.role, min_role):
            raise PermissionDenied(
                f"This action requires at least '{min_role.value}' role. "
                f"Your role: '{membership.role.value}'."
            )
        return membership

    return role_checker
