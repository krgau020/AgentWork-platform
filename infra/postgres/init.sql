-- =============================================================================
-- AgentWork Platform — PostgreSQL Schema
-- File: infra/postgres/init.sql
--
-- Purpose:
--     Defines all 10 tables for the AgentWork platform database.
--     This script runs automatically when the PostgreSQL Docker container
--     starts for the first time (pgdata volume is empty). It is mounted
--     into /docker-entrypoint-initdb.d/ in docker-compose.yml.
--
-- To re-run this script (e.g. after adding a table or column):
--     docker compose down -v     -- removes the pgdata named volume
--     docker compose up --build  -- fresh container, this script runs again
--
-- Table dependency order (FK references must exist before they can be used):
--     1. organizations         (no dependencies)
--     2. users                 (→ organizations)
--     3. tokens                (→ users)
--     4. groups                (→ organizations)
--     5. policies              (→ organizations)
--     6. policy_statements     (→ policies)
--     7. group_policies        (→ groups, policies)
--     8. user_groups           (→ users, groups)
--     9. invitations           (→ organizations, groups)
--    10. service_registry      (no dependencies)
--
-- Multi-tenancy model:
--     organizations is the root tenant boundary. Every user, group, and
--     policy belongs to exactly one organization. Data from one org is
--     never visible to another at the application layer.
--
-- Access control model (PBAC — Policy-Based Access Control):
--     User → user_groups → Group → group_policies → Policy → policy_statements
--     Each policy_statement is: (resource, action, effect=allow|deny)
--     The gateway evaluates these statements to authorize requests.
-- =============================================================================

-- Enable UUID generation (built-in on PostgreSQL 13+, needs pgcrypto on older)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";


-- =============================================================================
-- 1. organizations
--    Root tenant table. One row per company/team using the platform.
--    Created automatically when the first user signs up via auth-service.
-- =============================================================================
CREATE TABLE IF NOT EXISTS organizations (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL,
    slug        VARCHAR(100) NOT NULL UNIQUE,  -- URL-safe name, e.g. "acme-corp"
    is_active   BOOLEAN      NOT NULL DEFAULT true,
    created_at  TIMESTAMP    NOT NULL DEFAULT now()
);


-- =============================================================================
-- 2. users
--    One row per authenticated user. Email is globally unique (not per-org)
--    so a person's email cannot be registered under two different orgs.
--    org_id is nullable to support users created before the org-signup flow
--    was introduced; it should be populated for all new users.
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    email       VARCHAR(255) NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,         -- Argon2 hash, never plain text
    org_id      UUID         REFERENCES organizations(id),  -- nullable for legacy
    is_active   BOOLEAN      NOT NULL DEFAULT true,
    created_at  TIMESTAMP    NOT NULL DEFAULT now()
);


-- =============================================================================
-- 3. tokens
--    Server-side storage for active refresh tokens.
--    Presence in this table = token is valid and not yet revoked.
--    On logout:  the row is deleted → token is revoked.
--    On refresh: old row deleted, new row inserted (token rotation).
--    One user can have multiple rows (multiple devices / sessions).
-- =============================================================================
CREATE TABLE IF NOT EXISTS tokens (
    id            UUID  PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID  NOT NULL REFERENCES users(id),
    refresh_token TEXT  NOT NULL UNIQUE,  -- full JWT string
    created_at    TIMESTAMP NOT NULL DEFAULT now()
);


-- =============================================================================
-- 4. groups
--    Named collections of users within an organization.
--    Group names are unique per org (UNIQUE on org_id + name), so two orgs
--    can each have an "admin" group without conflict.
--    At signup, an "admin" group is created automatically for each new org.
-- =============================================================================
CREATE TABLE IF NOT EXISTS groups (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id      UUID         NOT NULL REFERENCES organizations(id),
    name        VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    created_at  TIMESTAMP    NOT NULL DEFAULT now(),
    UNIQUE (org_id, name)
);


-- =============================================================================
-- 5. policies
--    Named permission sets scoped to an organization.
--    A policy is a container for one or more policy_statements.
--    Policies are attached to groups (not directly to users) via group_policies.
-- =============================================================================
CREATE TABLE IF NOT EXISTS policies (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id      UUID         NOT NULL REFERENCES organizations(id),
    name        VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    created_at  TIMESTAMP    NOT NULL DEFAULT now(),
    UNIQUE (org_id, name)
);


-- =============================================================================
-- 6. policy_statements
--    Individual permission rules inside a policy.
--    Each row says: for resource X, action Y is allowed or denied.
--    Example:  resource="projects/*", action="read", effect="allow"
--              resource="projects/delete", action="delete", effect="deny"
--    The gateway evaluates all statements for a user's groups to decide
--    whether to forward a request.
-- =============================================================================
CREATE TABLE IF NOT EXISTS policy_statements (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id   UUID         NOT NULL REFERENCES policies(id),
    resource    VARCHAR(100) NOT NULL,
    action      VARCHAR(100) NOT NULL,
    effect      VARCHAR(10)  NOT NULL CHECK (effect IN ('allow', 'deny'))
);


-- =============================================================================
-- 7. group_policies  (join table: many groups ↔ many policies)
--    Links groups to policies. One group can have many policies.
--    One policy can be shared across many groups (e.g. a "read-only" policy
--    attached to both "viewer" and "billing" groups).
-- =============================================================================
CREATE TABLE IF NOT EXISTS group_policies (
    group_id    UUID NOT NULL REFERENCES groups(id),
    policy_id   UUID NOT NULL REFERENCES policies(id),
    PRIMARY KEY (group_id, policy_id)
);


-- =============================================================================
-- 8. user_groups  (join table: many users ↔ many groups)
--    Links users to groups within an org. A user can belong to multiple
--    groups. The auth-service reads this table at login to embed group names
--    into the JWT access token (groups claim).
-- =============================================================================
CREATE TABLE IF NOT EXISTS user_groups (
    user_id     UUID NOT NULL REFERENCES users(id),
    group_id    UUID NOT NULL REFERENCES groups(id),
    PRIMARY KEY (user_id, group_id)
);


-- =============================================================================
-- 9. invitations
--    One-time invite tokens created by admins and consumed by new users.
--    An admin creates an invite for a specific email + group. The invitee
--    submits the token to POST /api/v1/auth/accept-invite to create their
--    account and get placed in the target group automatically.
--
--    One-time use: the row is deleted by auth-service when the invite is
--    accepted — a replayed token finds no row and is rejected.
--    Expiry: expires_at is set 7 days from creation by invite_service.
--    Cascade: if the org or group is deleted, all their pending invites are
--    automatically deleted (ON DELETE CASCADE).
-- =============================================================================
CREATE TABLE IF NOT EXISTS invitations (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id      UUID         NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email       VARCHAR(255) NOT NULL,
    group_id    UUID         NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    token       TEXT         NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ  NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);


-- =============================================================================
-- 10. service_registry
--    Registry of solution microservices plugged into the platform.
--    The gateway reads this table to know which URL to proxy requests to
--    and which groups are allowed to access each service.
--
--    allowed_groups JSONB examples:
--      '["*"]'            — any authenticated user
--      '["admin"]'        — only users in the admin group
--      '["admin","ops"]'  — users in admin or ops groups
--
--    Services self-register by calling POST /registry/register on the gateway
--    at startup. last_heartbeat is updated periodically to track liveness.
-- =============================================================================
CREATE TABLE IF NOT EXISTS service_registry (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) NOT NULL UNIQUE,
    display_name    VARCHAR(255),
    base_url        VARCHAR(255) NOT NULL,
    route_prefix    VARCHAR(100) NOT NULL UNIQUE,
    allowed_groups  JSONB        NOT NULL DEFAULT '["*"]',
    health_endpoint VARCHAR(100) NOT NULL DEFAULT '/health',
    is_active       BOOLEAN      NOT NULL DEFAULT true,
    registered_at   TIMESTAMP    NOT NULL DEFAULT now(),
    last_heartbeat  TIMESTAMP
);
