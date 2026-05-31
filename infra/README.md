# infra/

Infrastructure configuration shared across all services.

---

## Folder Structure

```
infra/
└── postgres/
    └── init.sql    — Full database schema (all 9 tables)
```

---

## postgres/init.sql

This SQL script creates the entire AgentWork platform database schema.

**When does it run?**

PostgreSQL runs it automatically when the container starts for the **first time** — specifically when the `pgdata` named volume is empty. It is mounted into `/docker-entrypoint-initdb.d/` via `docker-compose.yml`.

```yaml
volumes:
  - ./infra/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
```

**How to re-run it (after a schema change):**

```bash
docker compose down -v       # removes the pgdata volume (wipes all data)
docker compose up --build    # fresh start — init.sql runs again
```

**Connect to the database:**

| Field | Value |
|-------|-------|
| Host | `localhost` |
| Port | `5432` |
| Database | `agentwork` |
| User | `admin` |
| Password | `admin` |

---

## Database Tables

All 9 tables, in creation order (FK dependencies respected):

| # | Table | Purpose |
|---|-------|---------|
| 1 | `organizations` | Root tenant. One row per company. Created at signup. |
| 2 | `users` | Registered users. Email globally unique. FK → organizations. |
| 3 | `tokens` | Active refresh tokens. Row = valid session. Deleted on logout/refresh. |
| 4 | `groups` | Named user groups per org (e.g. "admin", "viewer"). |
| 5 | `policies` | Named permission sets per org. Container for policy_statements. |
| 6 | `policy_statements` | Individual rules: resource + action + allow/deny. |
| 7 | `group_policies` | Links groups to policies (many-to-many). |
| 8 | `user_groups` | Links users to groups (many-to-many). Read at login to build JWT. |
| 9 | `service_registry` | Registered solution microservices — URL, route prefix, allowed groups. |

---

## Access Control Data Model (PBAC)

```
User
 └── user_groups (join)
      └── Group
           └── group_policies (join)
                └── Policy
                     └── policy_statements
                          └── { resource, action, effect: allow | deny }
```

The gateway reads a user's groups from the JWT, looks up their policies, and evaluates `policy_statements` to decide whether to forward the request.

---

## Multi-Tenancy

`organizations` is the root tenant boundary. Every row in every other table belongs to exactly one organization (directly or through the user → org chain). No cross-tenant data access at the application layer.

```
Organization
  ├── Users (org_id FK)
  ├── Groups (org_id FK)
  └── Policies (org_id FK)
```

---

## Useful DBeaver Queries

```sql
-- List all tables
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

-- See all organizations
SELECT id, name, slug, is_active FROM organizations;

-- See all users with their org
SELECT u.email, o.name AS org, u.is_active
FROM users u
JOIN organizations o ON u.org_id = o.id;

-- See a user's groups
SELECT u.email, g.name AS group_name
FROM users u
JOIN user_groups ug ON u.id = ug.user_id
JOIN groups g ON ug.group_id = g.id;

-- See active sessions (stored refresh tokens)
SELECT u.email, t.created_at
FROM tokens t
JOIN users u ON t.user_id = u.id;

-- See registered services
SELECT name, base_url, route_prefix, allowed_groups, is_active
FROM service_registry;
```
