# User Service

Manages everything inside an organization — groups, policies, and user assignments.
This is the platform's access control management layer. It never handles authentication.

Full architecture context: [architecture_steps_info/project-setup/5.user-service.md](../../architecture_steps_info/project-setup/5.user-service.md)

---

## What It Does

Three responsibilities — nothing else:

1. **Manage groups** — create groups, assign policies to groups
2. **Manage policies** — create policies, add permission statements (resource + action + effect)
3. **Manage user-group assignments** — put users into groups, remove them, resolve their effective permissions

No authentication. No JWT decoding. No password logic.
The gateway handles all of that before a request ever reaches this service.

---

## How It Gets Identity

The gateway validates the JWT and adds these headers to every request before forwarding here:

```
x-user-email:  alice@acme.com        ← who is making the request
x-org-id:      uuid-1                ← which tenant — every DB query filters by this
x-user-groups: admin                 ← is this person admin? Used for write access checks
x-request-id:  abc-123-xyz           ← for distributed tracing
```

This service reads `x-org-id` from the header for all data filtering, and checks `x-user-groups` for admin access on write operations.

---

## Folder Structure

```
services/user-service/
│
├── .env                        DB credentials
├── Dockerfile                  python:3.11-slim, uvicorn --reload
├── requirements.txt            fastapi, uvicorn, sqlalchemy, psycopg2-binary, pydantic-settings
│
└── app/
    ├── main.py                 FastAPI app, DB wait-for-startup, exception handler, health
    │
    ├── api/
    │   └── routes.py           All endpoints — orgs, users, groups, policies
    │                           Identity helpers: get_org_id(), require_admin()
    │
    ├── core/
    │   └── config.py           Pydantic BaseSettings — builds DATABASE_URL from env
    │
    ├── db/
    │   ├── base.py             SQLAlchemy DeclarativeBase — all models inherit from here
    │   └── session.py          Engine, SessionLocal, get_db() dependency
    │
    ├── models/                 ORM models — Python classes mapping to existing DB tables
    │   ├── organization.py     → organizations table (read-only here)
    │   ├── user.py             → users table (no password_hash column)
    │   ├── group.py            → groups table
    │   ├── policy.py           → policies + policy_statements tables
    │   ├── group_policy.py     → group_policies join table
    │   ├── user_group.py       → user_groups join table
    │   └── invitation.py       → invitations table (INSERT + READ)
    │
    ├── schemas/                Pydantic — request bodies and response shapes
    │   ├── organization.py     OrgResponse (returns org_id)
    │   ├── group.py            GroupCreate, GroupResponse (returns group_id), PolicyAssign
    │   ├── policy.py           PolicyCreate, PolicyUpdate, StatementCreate, StatementUpdate,
    │   │                       PolicyResponse (returns policy_id),
    │   │                       StatementResponse (returns statement_id)
    │   ├── user.py             UserResponse (returns user_id), GroupAssign, UserPoliciesResponse
    │   └── invite.py           InviteCreate, InviteResponse
    │
    └── services/               Business logic — DB queries
        ├── org_service.py      get_org
        ├── group_service.py    create_group, list_groups, assign_policy, remove_policy,
        │                       add_user_to_group, remove_user_from_group
        ├── policy_service.py   create_policy, update_policy, list_policies,
        │                       add_statement, update_statement, remove_statement
        ├── user_service.py     get_user, list_users, get_user_groups, get_user_policies
        └── invite_service.py   create_invite
```

---

## Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `POSTGRES_HOST` | `postgres` | Docker container name |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_USER` | `admin` | DB user |
| `POSTGRES_PASSWORD` | `admin` | DB password |
| `POSTGRES_DB` | `agentwork` | Database name |

---

## Running

```bash
# Start user-service only
docker compose up --build user-service

# Start all services
docker compose up --build

# Live logs
docker compose logs -f user-service

# Rebuild after requirements.txt change
docker compose up --build user-service
```

Code changes in `app/` are picked up automatically via `--reload` + volume mount.

---

## API Routes

All routes require `Authorization: Bearer <access_token>` header (validated by gateway).

### Organizations

| Method | Route | Who Can Call |
|--------|-------|--------------|
| GET | `/api/v1/orgs/{id}` | admin only |
| POST | `/api/v1/orgs/{id}/invites` | admin only |

### Groups

| Method | Route | Who Can Call |
|--------|-------|--------------|
| POST | `/api/v1/groups` | admin only |
| GET | `/api/v1/groups` | any authenticated user |
| POST | `/api/v1/groups/{id}/policies` | admin only |
| DELETE | `/api/v1/groups/{id}/policies/{policy_id}` | admin only |

### Policies

| Method | Route | Who Can Call |
|--------|-------|--------------|
| POST | `/api/v1/policies` | admin only |
| GET | `/api/v1/policies` | any authenticated user |
| PUT | `/api/v1/policies/{id}` | admin only |
| POST | `/api/v1/policies/{id}/statements` | admin only |
| PUT | `/api/v1/policies/{id}/statements/{statement_id}` | admin only |
| DELETE | `/api/v1/policies/{id}/statements/{statement_id}` | admin only |

### Users

| Method | Route | Who Can Call |
|--------|-------|--------------|
| GET | `/api/v1/users` | any authenticated user |
| GET | `/api/v1/users/{id}` | any authenticated user |
| POST | `/api/v1/users/{id}/groups` | admin only |
| DELETE | `/api/v1/users/{id}/groups/{group_id}` | admin only |
| GET | `/api/v1/users/{id}/groups` | any authenticated user |
| GET | `/api/v1/users/{id}/policies` | any authenticated user |

---

## Error Response Format

```json
{
  "error_code": "NOT_FOUND",
  "message": "Group not found",
  "request_id": "3f2a1b4c-8d2e-4f1a-b3c9-7e1d5f9a2c8b",
  "timestamp": "2026-05-22T10:24:37.540075+00:00"
}
```

| Status | error_code | When |
|--------|-----------|------|
| 400 | `VALIDATION_ERROR` | Invalid UUID in header |
| 403 | `ACCESS_DENIED` | Non-admin calling a write endpoint |
| 404 | `NOT_FOUND` | Resource does not exist in this org |
| 409 | `CONFLICT` | Duplicate — group name, policy name, or assignment already exists |

---

## PBAC Resolution Flow

```
GET /api/v1/users/{id}/policies

user_id → UserGroup rows → group_ids
          GroupPolicy rows → policy_ids
          Policy rows → policies
          PolicyStatement rows → statements per policy
          → returns: [{ policy_name, statements: [{resource, action, effect}] }]
```

This is the full permission chain. Downstream services call this endpoint to check
what a user is actually allowed to do.

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi` | Web framework |
| `uvicorn[standard]` | ASGI server |
| `pydantic-settings` | Config from .env |
| `sqlalchemy` | ORM — Python to SQL |
| `psycopg2-binary` | PostgreSQL driver |
| `python-dotenv` | .env file loading |
| `email-validator` | Required by Pydantic EmailStr in invite schemas |
| `redis` | Redis client — policy cache |

---

## Phase 4 — What Changed (Platform Hardening)

### Policy Cache (Point 2)

`GET /api/v1/users/{user_id}/policies` now caches results in Redis.

**Cache key:** `policy:{user_id}` | **TTL:** 300 seconds (5 minutes)

**Flow:**
```
Request → Redis GET policy:{user_id}
    HIT  → return cached JSON immediately (from_cache: true)
    MISS → query DB → write to Redis → return (from_cache: false)
```

**Invalidation:** When a user is added to or removed from a group (`POST/DELETE /api/v1/users/{id}/groups`), the cache key for that user is deleted immediately so the next policies call reflects the new membership.

Fail-open: if Redis is unavailable, the DB query runs normally — no error returned to the client.

### Structured JSON Logging (Point 3)

Every request logged as one JSON line with: `timestamp`, `service`, `level`, `message`, `method`, `path`, `status`, `duration_ms`, `request_id`.

The `request_id` from the gateway's `x-request-id` header is read and logged, enabling cross-service correlation:

```bash
# Find all logs for one request across services:
docker compose logs | Select-String "<request_id>"
```

---

## feature/policy-management — What Changed

### Policy Rename

`PUT /api/v1/policies/{policy_id}` — renames an existing policy.

- Body: `{ "name": "new-name" }`
- Returns: full `PolicyResponse` with updated name and existing statements
- 409 if the new name already exists in this org
- 404 if the policy does not exist or belongs to a different org

### Statement Edit In-Place

`PUT /api/v1/policies/{policy_id}/statements/{statement_id}` — updates all three fields of a statement without deleting and re-creating it.

- Body: `{ "resource": "platform:users", "action": "read", "effect": "allow" }`
- Returns: updated `StatementResponse`
- `statement_id` is preserved — existing group-policy assignments are not affected
- 404 if either the policy or the statement is not found under this org

### Frontend Changes

Policies page now supports inline editing:

- **Rename policy** — "Rename" button on each card header → inline input + Save/Cancel; Enter key saves, Escape cancels
- **Edit statement** — "Edit" button on each statement row → row switches to inputs + dropdowns; Save/Cancel inline
- State updates locally after save — no full page reload needed
