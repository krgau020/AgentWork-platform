"""Initial schema — all 10 tables

Revision ID: 0001
Revises:
Create Date: 2026-05-23

This migration creates the full AgentWork platform schema.
It uses IF NOT EXISTS on every table so it is safe to run against a database
that was already initialised by infra/postgres/init.sql — existing tables are
skipped, the alembic_version row is inserted, and the service continues.

Tables (in dependency order):
    1.  organizations
    2.  users
    3.  tokens
    4.  groups
    5.  policies
    6.  policy_statements
    7.  group_policies
    8.  user_groups
    9.  invitations
    10. service_registry
"""

from typing import Sequence, Union
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')

    op.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
            name        VARCHAR(255) NOT NULL,
            slug        VARCHAR(255) NOT NULL UNIQUE,
            created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
            email         VARCHAR(255) NOT NULL UNIQUE,
            password      TEXT         NOT NULL,
            org_id        UUID         REFERENCES organizations(id) ON DELETE SET NULL,
            is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
            created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            id             UUID  PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id        UUID  NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            refresh_token  TEXT  NOT NULL UNIQUE,
            created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id      UUID         NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            name        VARCHAR(100) NOT NULL,
            created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            UNIQUE (org_id, name)
        );
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS policies (
            id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id      UUID         NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            name        VARCHAR(255) NOT NULL,
            created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            UNIQUE (org_id, name)
        );
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS policy_statements (
            id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
            policy_id   UUID         NOT NULL REFERENCES policies(id) ON DELETE CASCADE,
            resource    VARCHAR(255) NOT NULL,
            action      VARCHAR(100) NOT NULL,
            effect      VARCHAR(10)  NOT NULL CHECK (effect IN ('allow', 'deny')),
            created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS group_policies (
            group_id    UUID NOT NULL REFERENCES groups(id)   ON DELETE CASCADE,
            policy_id   UUID NOT NULL REFERENCES policies(id) ON DELETE CASCADE,
            PRIMARY KEY (group_id, policy_id)
        );
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS user_groups (
            user_id     UUID NOT NULL REFERENCES users(id)  ON DELETE CASCADE,
            group_id    UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
            PRIMARY KEY (user_id, group_id)
        );
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS invitations (
            id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id      UUID         NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            email       VARCHAR(255) NOT NULL,
            group_id    UUID         NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
            token       TEXT         NOT NULL UNIQUE,
            expires_at  TIMESTAMPTZ  NOT NULL,
            created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS service_registry (
            id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
            service_name VARCHAR(100) NOT NULL UNIQUE,
            base_url     TEXT         NOT NULL,
            is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
            registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)


def downgrade() -> None:
    # Drop in reverse dependency order
    op.execute("DROP TABLE IF EXISTS service_registry;")
    op.execute("DROP TABLE IF EXISTS invitations;")
    op.execute("DROP TABLE IF EXISTS user_groups;")
    op.execute("DROP TABLE IF EXISTS group_policies;")
    op.execute("DROP TABLE IF EXISTS policy_statements;")
    op.execute("DROP TABLE IF EXISTS policies;")
    op.execute("DROP TABLE IF EXISTS groups;")
    op.execute("DROP TABLE IF EXISTS tokens;")
    op.execute("DROP TABLE IF EXISTS users;")
    op.execute("DROP TABLE IF EXISTS organizations;")
