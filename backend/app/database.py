"""
Async SQLAlchemy database engine, session factory, and tenant-aware session.

Tenant isolation is enforced at two levels:
  1. Application: every repository query includes org_id WHERE clause
  2. Database: PostgreSQL RLS policies filter rows by app.current_tenant

SET LOCAL scopes the GUC variable to the current transaction only,
preventing tenant leakage across connection-pooled requests.
"""

from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text
from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)

AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session():
    """Yield a plain async session (no tenant context). Used for auth flows."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_tenant_session(org_id: str):
    """
    Yield a tenant-scoped async session.

    Sets PostgreSQL session variable for Row-Level Security.
    SET LOCAL is used intentionally: it scopes the variable to the
    current transaction only, so it cannot leak to other requests
    sharing the same pooled connection.

    The application role 'taskforge_app' has NO BYPASSRLS privilege,
    ensuring the database enforces tenant isolation even if application
    code has a bug.
    """
    async with AsyncSessionFactory() as session:
        try:
            # Begin an explicit transaction so SET LOCAL has scope
            await session.begin()

            # Inject tenant context for RLS
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
