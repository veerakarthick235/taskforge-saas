-- ============================================================
-- TaskForge Row-Level Security Policies
-- Run AFTER Alembic creates the tables, using the superuser.
-- The application connects as 'taskforge_app' (no BYPASSRLS).
-- ============================================================

-- ──────────── Enable RLS on all tenant-scoped tables ────────────

ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks FORCE ROW LEVEL SECURITY;    -- even table owner is subject

ALTER TABLE invites ENABLE ROW LEVEL SECURITY;
ALTER TABLE invites FORCE ROW LEVEL SECURITY;

ALTER TABLE activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_logs FORCE ROW LEVEL SECURITY;


-- ──────────── TASKS ────────────

-- SELECT: tenant can only read its own tasks
CREATE POLICY tenant_tasks_select ON tasks
    FOR SELECT
    USING (org_id = current_setting('app.current_tenant', true)::uuid);

-- INSERT: tenant can only insert tasks with its own org_id
CREATE POLICY tenant_tasks_insert ON tasks
    FOR INSERT
    WITH CHECK (org_id = current_setting('app.current_tenant', true)::uuid);

-- UPDATE: tenant can only update its own tasks
CREATE POLICY tenant_tasks_update ON tasks
    FOR UPDATE
    USING (org_id = current_setting('app.current_tenant', true)::uuid)
    WITH CHECK (org_id = current_setting('app.current_tenant', true)::uuid);

-- DELETE: tenant can only delete its own tasks
CREATE POLICY tenant_tasks_delete ON tasks
    FOR DELETE
    USING (org_id = current_setting('app.current_tenant', true)::uuid);


-- ──────────── INVITES ────────────

CREATE POLICY tenant_invites_select ON invites
    FOR SELECT
    USING (org_id = current_setting('app.current_tenant', true)::uuid);

CREATE POLICY tenant_invites_insert ON invites
    FOR INSERT
    WITH CHECK (org_id = current_setting('app.current_tenant', true)::uuid);

CREATE POLICY tenant_invites_update ON invites
    FOR UPDATE
    USING (org_id = current_setting('app.current_tenant', true)::uuid)
    WITH CHECK (org_id = current_setting('app.current_tenant', true)::uuid);

CREATE POLICY tenant_invites_delete ON invites
    FOR DELETE
    USING (org_id = current_setting('app.current_tenant', true)::uuid);


-- ──────────── ACTIVITY LOGS ────────────

CREATE POLICY tenant_activity_select ON activity_logs
    FOR SELECT
    USING (org_id = current_setting('app.current_tenant', true)::uuid);

CREATE POLICY tenant_activity_insert ON activity_logs
    FOR INSERT
    WITH CHECK (org_id = current_setting('app.current_tenant', true)::uuid);

-- Activity logs are append-only: no update or delete policies granted.


-- ──────────── VERIFY ────────────
-- Run to confirm RLS is active:
-- SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';
