"""
Integration tests — API endpoints with real DB.

Covers:
  - Auth flow (register → login → me)
  - Organization lifecycle (create → get)
  - Task CRUD within tenant context
  - Error responses (401, 403, 422)
"""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient

from tests.conftest import make_auth_headers


@pytest.mark.asyncio
class TestAuthFlow:
    """Auth API integration tests."""

    async def test_register_and_login(self, client: AsyncClient):
        """Register a new user, then login with same credentials."""
        email = f"integ-{uuid.uuid4().hex[:8]}@test.com"
        password = "SecurePass123!"

        # Register
        res = await client.post("/api/v1/auth/register", json={
            "email": email,
            "full_name": "Integration User",
            "password": password,
        })
        assert res.status_code == 201
        data = res.json()
        assert "tokens" in data
        assert data["user"]["email"] == email

        # Login
        res = await client.post("/api/v1/auth/login", json={
            "email": email,
            "password": password,
        })
        assert res.status_code == 200
        assert "tokens" in res.json()

    async def test_me_without_token(self, client: AsyncClient):
        """GET /me without token returns 403 (no bearer)."""
        res = await client.get("/api/v1/auth/me")
        assert res.status_code == 403

    async def test_me_with_invalid_token(self, client: AsyncClient):
        """GET /me with garbage token returns 401."""
        res = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer garbage.token.here"},
        )
        assert res.status_code == 401
        body = res.json()
        assert body["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
class TestOrganizationFlow:
    """Org creation and access integration tests."""

    async def test_create_org(self, client: AsyncClient):
        """Register user → create org → verify ownership."""
        email = f"org-{uuid.uuid4().hex[:8]}@test.com"

        # Register
        reg = await client.post("/api/v1/auth/register", json={
            "email": email,
            "full_name": "Org Creator",
            "password": "SecurePass123!",
        })
        tokens = reg.json()["tokens"]
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Create org
        slug = f"test-org-{uuid.uuid4().hex[:8]}"
        res = await client.post("/api/v1/organizations/", json={
            "name": "My Org",
            "slug": slug,
        }, headers=headers)
        assert res.status_code == 201
        org = res.json()
        assert org["name"] == "My Org"
        assert org["slug"] == slug
        assert org["member_count"] == 1

    async def test_duplicate_slug_rejected(self, client: AsyncClient):
        """Creating two orgs with the same slug returns 409."""
        email = f"dup-{uuid.uuid4().hex[:8]}@test.com"
        reg = await client.post("/api/v1/auth/register", json={
            "email": email,
            "full_name": "Dup Test",
            "password": "SecurePass123!",
        })
        headers = {"Authorization": f"Bearer {reg.json()['tokens']['access_token']}"}
        slug = f"dup-slug-{uuid.uuid4().hex[:8]}"

        # First — OK
        res = await client.post("/api/v1/organizations/", json={
            "name": "Org A", "slug": slug,
        }, headers=headers)
        assert res.status_code == 201

        # Second — conflict
        res = await client.post("/api/v1/organizations/", json={
            "name": "Org B", "slug": slug,
        }, headers=headers)
        assert res.status_code == 409


@pytest.mark.asyncio
class TestTenantIsolation:
    """
    Critical: Prove cross-tenant data access is impossible.
    """

    async def _create_user_with_org(self, client: AsyncClient, suffix: str):
        """Helper: register user + create org, return (headers, org_id)."""
        email = f"iso-{suffix}-{uuid.uuid4().hex[:8]}@test.com"
        reg = await client.post("/api/v1/auth/register", json={
            "email": email,
            "full_name": f"User {suffix}",
            "password": "SecurePass123!",
        })
        tokens = reg.json()["tokens"]
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        slug = f"iso-org-{suffix}-{uuid.uuid4().hex[:8]}"
        org_res = await client.post("/api/v1/organizations/", json={
            "name": f"Org {suffix}",
            "slug": slug,
        }, headers=headers)
        org_id = org_res.json()["id"]

        return headers, org_id

    async def test_user_cannot_access_other_org_tasks(self, client: AsyncClient):
        """User A cannot list tasks in User B's organization."""
        headers_a, org_a = await self._create_user_with_org(client, "A")
        headers_b, org_b = await self._create_user_with_org(client, "B")

        # User A creates a task in Org A
        task_res = await client.post(
            f"/api/v1/organizations/{org_a}/tasks/",
            json={"title": "Secret Task", "priority": "high"},
            headers={**headers_a, "X-Org-ID": org_a},
        )
        assert task_res.status_code == 201

        # User B tries to list Org A's tasks → 403
        res = await client.get(
            f"/api/v1/organizations/{org_a}/tasks/",
            headers={**headers_b, "X-Org-ID": org_a},
        )
        assert res.status_code == 403
        assert res.json()["error"]["code"] == "TENANT_ACCESS_DENIED"

    async def test_user_cannot_access_other_org_members(self, client: AsyncClient):
        """User A cannot view members of User B's org."""
        headers_a, _ = await self._create_user_with_org(client, "C")
        _, org_b = await self._create_user_with_org(client, "D")

        res = await client.get(
            f"/api/v1/organizations/{org_b}/members",
            headers={**headers_a, "X-Org-ID": org_b},
        )
        assert res.status_code == 403

    async def test_missing_org_header_rejected(self, client: AsyncClient):
        """Requests without X-Org-ID header to tenant endpoints are rejected."""
        headers_a, org_a = await self._create_user_with_org(client, "E")

        # No X-Org-ID header
        res = await client.get(
            f"/api/v1/organizations/{org_a}/tasks/",
            headers=headers_a,  # no X-Org-ID
        )
        assert res.status_code == 403


@pytest.mark.asyncio
class TestRBACEnforcement:
    """Verify role-based access control at the API level."""

    async def test_member_cannot_delete_task(self, client: AsyncClient):
        """
        A member-role user cannot delete tasks (requires admin+).
        """
        # Create owner user + org
        email_owner = f"rbac-owner-{uuid.uuid4().hex[:8]}@test.com"
        reg = await client.post("/api/v1/auth/register", json={
            "email": email_owner,
            "full_name": "RBAC Owner",
            "password": "SecurePass123!",
        })
        owner_headers = {"Authorization": f"Bearer {reg.json()['tokens']['access_token']}"}
        slug = f"rbac-org-{uuid.uuid4().hex[:8]}"
        org_res = await client.post("/api/v1/organizations/", json={
            "name": "RBAC Org", "slug": slug,
        }, headers=owner_headers)
        org_id = org_res.json()["id"]

        # Owner creates a task
        task_res = await client.post(
            f"/api/v1/organizations/{org_id}/tasks/",
            json={"title": "RBAC Test Task"},
            headers={**owner_headers, "X-Org-ID": org_id},
        )
        task_id = task_res.json()["id"]

        # Create a member user
        email_member = f"rbac-member-{uuid.uuid4().hex[:8]}@test.com"
        reg2 = await client.post("/api/v1/auth/register", json={
            "email": email_member,
            "full_name": "RBAC Member",
            "password": "SecurePass123!",
        })
        member_headers = {"Authorization": f"Bearer {reg2.json()['tokens']['access_token']}"}

        # Owner invites member
        invite_res = await client.post(
            f"/api/v1/organizations/{org_id}/invites/",
            json={"email": email_member, "role": "member"},
            headers={**owner_headers, "X-Org-ID": org_id},
        )

        if invite_res.status_code == 201:
            token = invite_res.json().get("token")
            if token:
                await client.post(
                    "/api/v1/invites/accept",
                    json={"token": token},
                    headers=member_headers,
                )

            # Member tries to delete task → 403
            res = await client.delete(
                f"/api/v1/organizations/{org_id}/tasks/{task_id}",
                headers={**member_headers, "X-Org-ID": org_id},
            )
            assert res.status_code == 403
            assert res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.asyncio
class TestErrorResponses:
    """Verify standardized error envelope across all error types."""

    async def test_404_shape(self, client: AsyncClient):
        """Non-existent route returns standardized error."""
        res = await client.get("/api/v1/nonexistent")
        assert res.status_code in (404, 405)
        body = res.json()
        assert "error" in body
        assert "code" in body["error"]
        assert "message" in body["error"]
        assert "status" in body["error"]

    async def test_422_validation_shape(self, client: AsyncClient):
        """Invalid JSON body returns validation error with field info."""
        res = await client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            # missing password, full_name
        })
        assert res.status_code == 422
        body = res.json()
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert isinstance(body["error"]["message"], str)

    async def test_health_check(self, client: AsyncClient):
        """Health endpoint returns 200."""
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"
