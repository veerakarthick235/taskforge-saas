"""
Test configuration — shared fixtures for the TaskForge test suite.

Uses a separate test database with full RLS enabled.
Each test runs in a transaction that rolls back on teardown.

NOTE: DB fixtures are only available when asyncpg is installed.
      Unit tests (test_unit_*.py) run without a database.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator

import pytest

try:
    import asyncpg  # noqa: F401
    HAS_DB = True
except ImportError:
    HAS_DB = False


# ─── DB-dependent fixtures (only load when asyncpg is available) ───

if HAS_DB:
    import pytest_asyncio
    from httpx import AsyncClient, ASGITransport
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    from sqlalchemy import text

    from app.config import settings
    from app.database import AsyncSessionFactory
    from app.main import app
    from app.models.base import Base
    from app.models.user import User
    from app.models.organization import Organization
    from app.models.membership import Membership, MemberRole
    from app.models.task import Task, TaskStatus, TaskPriority
    from app.utils.security import hash_password, create_access_token

    # ─── Test DB Engine ───

    TEST_DB_URL = settings.DATABASE_URL
    test_engine = create_async_engine(TEST_DB_URL, echo=False)
    TestSessionFactory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    # ─── Event loop ───

    @pytest.fixture(scope="session")
    def event_loop():
        loop = asyncio.new_event_loop()
        yield loop
        loop.close()

    # ─── Create tables once per session ───

    @pytest_asyncio.fixture(scope="session", autouse=True)
    async def setup_database():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    # ─── DB session per test (rolled back) ───

    @pytest_asyncio.fixture
    async def db_session() -> AsyncGenerator[AsyncSession, None]:
        async with TestSessionFactory() as session:
            async with session.begin():
                yield session
            # Implicit rollback on exit (no commit)

    # ─── Seed data factories ───

    @pytest_asyncio.fixture
    async def seed_user(db_session: AsyncSession) -> User:
        """Create a test user."""
        user = User(
            id=uuid.uuid4(),
            email=f"test-{uuid.uuid4().hex[:8]}@example.com",
            full_name="Test User",
            password_hash=hash_password("TestPass123!"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.flush()
        return user

    @pytest_asyncio.fixture
    async def seed_org(db_session: AsyncSession, seed_user: User) -> Organization:
        """Create a test organization."""
        org = Organization(
            id=uuid.uuid4(),
            name="Test Org",
            slug=f"test-org-{uuid.uuid4().hex[:8]}",
            created_by=seed_user.id,
        )
        db_session.add(org)
        await db_session.flush()

        membership = Membership(
            id=uuid.uuid4(),
            user_id=seed_user.id,
            org_id=org.id,
            role=MemberRole.OWNER,
        )
        db_session.add(membership)
        await db_session.flush()
        return org

    @pytest_asyncio.fixture
    async def seed_task(db_session: AsyncSession, seed_user: User, seed_org: Organization) -> Task:
        """Create a test task."""
        task = Task(
            id=uuid.uuid4(),
            org_id=seed_org.id,
            title="Test Task",
            description="Test description",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            created_by=seed_user.id,
            position=1,
        )
        db_session.add(task)
        await db_session.flush()
        return task

    def make_auth_headers(user: User, org: Organization = None) -> dict:
        """Generate auth headers with a valid JWT for the given user."""
        token = create_access_token(str(user.id))
        headers = {"Authorization": f"Bearer {token}"}
        if org:
            headers["X-Org-ID"] = str(org.id)
        return headers

    # ─── HTTP Client ───

    @pytest_asyncio.fixture
    async def client() -> AsyncGenerator[AsyncClient, None]:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c
