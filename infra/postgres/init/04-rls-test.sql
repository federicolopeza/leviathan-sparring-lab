-- Phase 5 RLS verification for V-T7-003 and V-T4-008.
-- V-T7-003 keeps one shared melispy_app role across services; these checks verify
-- that RLS still blocks cross-tenant reads when the role is scoped to org-A.
-- V-T4-008 remains relevant because SQL injection can still alter session context
-- or set app.bypass_rls, so this script explicitly turns bypass off before reads.

-- Check indexed_documents in the search-service database.
\c melispy_search

BEGIN;
SET LOCAL ROLE melispy_app;
SET LOCAL app.current_org_id = 'org-A';
SET LOCAL app.bypass_rls = 'on';

-- Seed two tenants while the admin bypass is enabled; this models setup/migration
-- behavior and avoids the RLS WITH CHECK policy rejecting the org-B fixture.
INSERT INTO indexed_documents (id, org_id, title, body, tags, created_at, updated_at)
VALUES
    ('rls-test-search-org-a', 'org-A', 'Phase 5 org-A document', 'visible to org-A', '[]'::json, now(), now()),
    ('rls-test-search-org-b', 'org-B', 'Phase 5 org-B document', 'must be hidden from org-A', '[]'::json, now(), now())
ON CONFLICT (id) DO UPDATE
SET org_id = EXCLUDED.org_id,
    title = EXCLUDED.title,
    body = EXCLUDED.body,
    tags = EXCLUDED.tags,
    updated_at = EXCLUDED.updated_at;

SET LOCAL app.bypass_rls = 'off';

-- V-T7-003 assertion: the shared melispy_app role must see only org-A rows.
-- If org-B is visible here, cross-tenant reads are not being filtered.
DO $$
DECLARE
    visible_count integer;
    org_b_count integer;
BEGIN
    SELECT count(*) INTO visible_count
    FROM indexed_documents
    WHERE id IN ('rls-test-search-org-a', 'rls-test-search-org-b');

    SELECT count(*) INTO org_b_count
    FROM indexed_documents
    WHERE id = 'rls-test-search-org-b';

    IF visible_count <> 1 OR org_b_count <> 0 THEN
        RAISE EXCEPTION
            'indexed_documents RLS failure: expected only org-A row, got visible_count=%, org_b_count=%',
            visible_count,
            org_b_count;
    END IF;
END;
$$;

ROLLBACK;

-- Check org_memberships in the orgs-service database.
\c melispy_orgs

BEGIN;
SET LOCAL ROLE melispy_app;
SET LOCAL app.current_org_id = 'org-A';
SET LOCAL app.bypass_rls = 'on';

-- Seed parent org rows required by the org_memberships foreign key.
INSERT INTO orgs (id, name, plan, region, owner_user_id, created_at, updated_at)
VALUES
    ('org-A', 'Phase 5 Org A', 'free', 'sa-east-1', 'rls-test-owner-a', now(), now()),
    ('org-B', 'Phase 5 Org B', 'free', 'sa-east-1', 'rls-test-owner-b', now(), now())
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    plan = EXCLUDED.plan,
    region = EXCLUDED.region,
    owner_user_id = EXCLUDED.owner_user_id,
    updated_at = EXCLUDED.updated_at;

-- Seed two memberships across tenants while bypass is enabled.
INSERT INTO org_memberships (id, org_id, user_id, role, created_at)
VALUES
    ('rls-test-membership-org-a', 'org-A', 'rls-test-user-a', 'member', now()),
    ('rls-test-membership-org-b', 'org-B', 'rls-test-user-b', 'member', now())
ON CONFLICT (org_id, user_id) DO UPDATE
SET role = EXCLUDED.role;

SET LOCAL app.bypass_rls = 'off';

-- V-T7-003 assertion: org-B membership must not be readable from org-A context.
-- V-T4-008 remains the bypass path if attacker-controlled SQL can alter settings.
DO $$
DECLARE
    visible_count integer;
    org_b_count integer;
BEGIN
    SELECT count(*) INTO visible_count
    FROM org_memberships
    WHERE id IN ('rls-test-membership-org-a', 'rls-test-membership-org-b');

    SELECT count(*) INTO org_b_count
    FROM org_memberships
    WHERE id = 'rls-test-membership-org-b';

    IF visible_count <> 1 OR org_b_count <> 0 THEN
        RAISE EXCEPTION
            'org_memberships RLS failure: expected only org-A row, got visible_count=%, org_b_count=%',
            visible_count,
            org_b_count;
    END IF;
END;
$$;

ROLLBACK;
