-- ============================================================
-- TaskForge Indexing Strategy
-- Composite and partial indexes for tenant-aware hot paths.
-- Run AFTER Alembic creates the tables.
-- ============================================================

-- ──────────── TASKS ────────────

-- Primary hot path: list tasks for an org, filtered by status, ordered by position
-- Covers: GET /organizations/{org_id}/tasks/?status=...
-- Also used by RLS policy (org_id match) + soft-delete filter
CREATE INDEX CONCURRENTLY IF NOT EXISTS
    ix_tasks_org_status_position
    ON tasks (org_id, status, position)
    WHERE deleted_at IS NULL;

-- Filter by priority within a tenant
CREATE INDEX CONCURRENTLY IF NOT EXISTS
    ix_tasks_org_priority
    ON tasks (org_id, priority)
    WHERE deleted_at IS NULL;

-- Filter by assignee within a tenant
CREATE INDEX CONCURRENTLY IF NOT EXISTS
    ix_tasks_org_assignee
    ON tasks (org_id, assignee_id)
    WHERE deleted_at IS NULL;

-- Overdue query: due_date < today, status != done, within a tenant
CREATE INDEX CONCURRENTLY IF NOT EXISTS
    ix_tasks_org_due_date
    ON tasks (org_id, due_date)
    WHERE deleted_at IS NULL AND due_date IS NOT NULL;

-- Full-text search on title within a tenant (trigram)
-- Requires: CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- Supports: ILIKE '%search%' queries the task list uses
CREATE INDEX CONCURRENTLY IF NOT EXISTS
    ix_tasks_title_trgm
    ON tasks USING gin (title gin_trgm_ops);


-- ──────────── MEMBERSHIPS ────────────

-- Primary hot path: check membership for a (user, org) pair
-- Covers: get_membership dependency (called on every tenant-scoped request)
CREATE INDEX CONCURRENTLY IF NOT EXISTS
    ix_memberships_user_org
    ON memberships (user_id, org_id)
    WHERE deleted_at IS NULL;

-- List all orgs for a user (org switcher dropdown)
CREATE INDEX CONCURRENTLY IF NOT EXISTS
    ix_memberships_user_active
    ON memberships (user_id)
    WHERE deleted_at IS NULL;

-- List all members of an org (members page)
CREATE INDEX CONCURRENTLY IF NOT EXISTS
    ix_memberships_org_active
    ON memberships (org_id)
    WHERE deleted_at IS NULL;


-- ──────────── INVITES ────────────

-- Lookup pending invites for an org (admin invite list)
CREATE INDEX CONCURRENTLY IF NOT EXISTS
    ix_invites_org_status
    ON invites (org_id, status);

-- Token lookup (accept invite flow) — already has unique index on token


-- ──────────── ACTIVITY LOGS ────────────

-- Activity feed: paginated by created_at within a tenant
CREATE INDEX CONCURRENTLY IF NOT EXISTS
    ix_activity_org_created
    ON activity_logs (org_id, created_at DESC);


-- ──────────── USERS ────────────

-- Auth lookup by email — already has unique index on email
-- JWT lookup by id — uses primary key


-- ──────────── VERIFY ────────────
-- SELECT indexname, tablename FROM pg_indexes WHERE schemaname = 'public' ORDER BY tablename;
