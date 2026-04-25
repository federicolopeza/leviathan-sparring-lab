-- Phase 5 defense: Row-Level Security on indexed_documents and org_memberships
-- This makes V-T7-003 (shared role) harder to exploit for cross-tenant reads.
-- V-T7-003 is still baked as a finding — the shared role itself is intentional —
-- but RLS adds a defense layer that only a SQL injection (V-T4-008) bypasses.

-- Set up session variable used by RLS policies
-- Each service sets: SET LOCAL app.current_org_id = '<org_id>'

-- Enable RLS on indexed_documents (search-service DB)
\c melispy_search
ALTER TABLE indexed_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE indexed_documents FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON indexed_documents
    USING (
        org_id IS NULL -- public documents
        OR org_id::text = current_setting('app.current_org_id', true)
        OR current_setting('app.bypass_rls', true) = 'on' -- admin bypass
    );

-- melispy_app bypasses RLS by default for backwards compat
-- V-T7-003 intentional: shared role still bypasses RLS unless FORCE is set
ALTER ROLE melispy_app SET row_security = on;

-- Enable RLS on org_memberships (orgs-service DB)
\c melispy_orgs
ALTER TABLE org_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE org_memberships FORCE ROW LEVEL SECURITY;

CREATE POLICY org_tenant_isolation ON org_memberships
    USING (
        org_id::text = current_setting('app.current_org_id', true)
        OR current_setting('app.bypass_rls', true) = 'on'
    );

-- Superuser (melispy_admin) bypasses RLS for migrations
-- melispy_app subject to RLS
GRANT ALL ON org_memberships TO melispy_app;
