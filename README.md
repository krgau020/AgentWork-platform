# AgentWork Platform

Multi-tenant SaaS infrastructure for AI-powered solutions. The platform handles authentication, authorization, request routing, and policy-based access control. Solution microservices plug in via the service registry — no platform code change needed to add a new service.

---

## Platform Architecture

```
                    ┌───────────────────────┐
                    │   Browser / Client    │
                    └───────┬───────┬───────┘
                            │       │ API calls (fetch)
                    page    │       │ directly to gateway
                    load    │       │
                            ▼       ▼
              ┌─────────────────┐  ┌──────────────────────┐
              │  Next.js        │  │   API Gateway :8000   │
              │  Frontend :3000 │  │                       │
              │                 │  │  JWT validation        │
              │  Admin dashboard│  │  Rate limiting (Redis) │
              │  Login / Signup │  │  Request tracing       │
              │  Policy mgmt    │  │  CORS                  │
              └─────────────────┘  └────────┬─────────┬────┘
                                            │         │
                               ┌────────────▼──┐  ┌───▼──────────────┐
                               │ Auth Service  │  │  User Service    │
                               │   :8001       │  │    :8003         │
                               │               │  │                  │
                               │ signup/login  │  │ orgs / groups /  │
                               │ refresh/logout│  │ policies / users │
                               │ accept-invite │  │ invitations      │
                               │ Alembic runs  │  │ Policy cache     │
                               │ at startup    │  │ (Redis)          │
                               └──────┬────────┘  └──────┬───────────┘
                                      │                   │
                               ┌──────▼───────────────────▼───────────┐
                               │        PostgreSQL :5432               │
                               │        Redis      :6379               │
                               └──────────────────────────────────────┘
```

### Access Control Model (PBAC — Policy-Based Access Control)

Users do not have a role column. Instead:

```
User → user_groups → Groups → group_policies → Policies → policy_statements
                                                           (resource, action, effect)
```

At login, the auth service resolves the user's groups and embeds them in the JWT. The gateway reads `org_id` and `groups` from the token and forwards them as headers to every downstream service — no DB call per request.

---

## Services

| Service      | Port | Container                | Responsibility                                         | Status       |
|--------------|------|--------------------------|--------------------------------------------------------|--------------|
| Frontend     | 3000 | `agentwork_frontend`     | Next.js admin UI — login, dashboard, PBAC management  | **Complete** |
| API Gateway  | 8000 | `agentwork_gateway`      | JWT validation, routing, rate limiting, tracing        | **Complete** |
| Auth Service | 8001 | `agentwork_auth_service` | Signup, login, refresh, logout, accept-invite, Alembic | **Complete** |
| User Service | 8003 | `agentwork_user_service` | Orgs, groups, policies, user management, invites       | **Complete** |

## Infrastructure

| Component  | Port | Container            | Purpose                                                  |
|------------|------|----------------------|----------------------------------------------------------|
| PostgreSQL | 5432 | `agentwork_postgres` | Platform database — 10 tables, managed by Alembic        |
| Redis      | 6379 | `agentwork_redis`    | Rate limit counters (gateway) + policy cache (user-svc)  |

> PostgreSQL and Redis are internal. Do not call them directly from solution services.

---

## Quick Start

```bash
# Start all backend services (gateway + auth + user + postgres + redis)
docker compose up --build

# Start everything including the frontend
docker compose --profile frontend up --build

# Rebuild a single service after code changes
docker compose up --build auth-service

# View live logs
docker compose logs -f gateway
docker compose logs -f auth-service

# Stop everything
docker compose down

# Stop and wipe all data (DB resets, Alembic re-runs migration 0001 on next start)
docker compose down -v
```

### Verify startup

```
GET http://localhost:8000/health  →  {"status": "ok", "service": "gateway"}
GET http://localhost:8001/health  →  {"status": "ok", "service": "auth-service"}
GET http://localhost:8003/health  →  {"status": "ok", "service": "user-service"}
```

### Frontend access

```
http://localhost:3000          →  redirects to /login
http://localhost:3000/login    →  sign in to existing account
http://localhost:3000/signup   →  create a new org + admin account
http://localhost:3000/invite   →  accept an invite token (from ?token= query param)
http://localhost:3000/dashboard →  admin dashboard (requires login)
```

---

## Frontend — Pages

The frontend is a Next.js 14 (App Router) admin dashboard. All API calls go directly from the browser to the gateway at `:8000`.

| Route | Who can access | What it does |
|---|---|---|
| `/login` | Anyone | Sign in with email + password |
| `/signup` | Anyone | Create a new organization + admin account |
| `/invite?token=` | Invitee | Accept invite token, set password, auto-login |
| `/dashboard` | Any authenticated user | Stats overview — user/group/policy counts, session info |
| `/dashboard/users` | Any authenticated user | List org users; admin can manage group memberships |
| `/dashboard/groups` | Any authenticated user | List groups; admin can create groups + assign policies |
| `/dashboard/policies` | Any authenticated user | List policies + statements; admin can create + modify |
| `/dashboard/invites` | Admin only | Create invite tokens for new org members |

**Auth behavior:**
- JWT decoded client-side (base64url) — no `/me` endpoint needed
- 401 responses trigger a silent token refresh; if refresh fails, redirects to `/login`
- Admin-only features (create, manage, invite) hidden from non-admin users at the UI level

---

## Database Schema — 10 Tables

```
organizations       → root tenant boundary — one row per company/team
users               → platform users, each scoped to one org
tokens              → active refresh tokens (server-side revocation)
groups              → named collections of users within an org
policies            → named permission sets within an org
policy_statements   → individual rules: resource + action + allow/deny
group_policies      → which policies a group has (join table)
user_groups         → which groups a user belongs to (join table)
invitations         → one-time invite tokens for adding users to an org
service_registry    → registered solution microservices and routing config
```

**Schema management — Alembic:**

Schema is managed by versioned Alembic migrations in `services/auth-service/alembic/versions/`. On every auth-service startup, `alembic upgrade head` runs automatically and is idempotent — safe to run on every restart.

```
auth-service startup sequence:
  1. wait_for_db()       — polls PostgreSQL until ready (10 retries, 2s apart)
  2. run_migrations()    — alembic upgrade head (checks alembic_version, skips if current)
  3. FastAPI starts      — begins serving requests
```

`infra/postgres/init.sql` initialises the DB on the first container start. Alembic and init.sql are kept in sync.

---

## Complete API Reference

All routes go through the gateway at port **8000**. The gateway validates JWT and forwards to the correct service.

### Auth Routes — Public (no JWT required)

Full documentation: [services/auth-service/README.md](services/auth-service/README.md)

| Method | Route                          | Body                                  | Returns                                             |
|--------|--------------------------------|---------------------------------------|-----------------------------------------------------|
| POST   | `/api/v1/auth/signup`          | `{ email, password, org_name }`       | `{ message: "User created successfully" }`          |
| POST   | `/api/v1/auth/login`           | `{ email, password }`                 | `{ access_token, refresh_token }`                   |
| POST   | `/api/v1/auth/refresh`         | `{ refresh_token }`                   | `{ access_token, refresh_token }` (old token revoked)|
| POST   | `/api/v1/auth/logout`          | `{ refresh_token }`                   | `{ message: "Logged out successfully" }`            |
| POST   | `/api/v1/auth/accept-invite`   | `{ invite_token, password }`          | `{ access_token, refresh_token }`                   |

**JWT payload:**
```json
{
  "sub":    "alice@acme.com",
  "org_id": "550e8400-e29b-41d4-a716-446655440000",
  "groups": ["admin"],
  "exp":    1748000000
}
```

- `access_token` — 2 hours, send as `Authorization: Bearer <token>` on every API call
- `refresh_token` — 7 days, use only to call `/refresh`, stored in DB for revocation

---

### User-Service Routes — Protected (JWT required)

Full documentation: [services/user-service/README.md](services/user-service/README.md)

The gateway validates the JWT, then injects identity headers before forwarding. All routes are scoped to the caller's `org_id` — cross-org access is impossible.

**"any"** = any authenticated user (valid JWT).
**"admin"** = `x-user-groups` header must contain `"admin"`.

#### Organizations

| Method | Route                           | Who   | Description                    |
|--------|---------------------------------|-------|--------------------------------|
| GET    | `/api/v1/orgs/{org_id}`         | admin | Get org details                |
| POST   | `/api/v1/orgs/{org_id}/invites` | admin | Create one-time invite token   |

#### Groups

| Method | Route                                       | Who   | Description              |
|--------|---------------------------------------------|-------|--------------------------|
| POST   | `/api/v1/groups`                            | admin | Create group             |
| GET    | `/api/v1/groups`                            | any   | List groups (paginated)  |
| POST   | `/api/v1/groups/{group_id}/policies`        | admin | Assign policy to group   |
| DELETE | `/api/v1/groups/{group_id}/policies/{p_id}` | admin | Remove policy from group |

#### Policies

| Method | Route                                           | Who   | Description                |
|--------|-------------------------------------------------|-------|----------------------------|
| POST   | `/api/v1/policies`                              | admin | Create policy              |
| GET    | `/api/v1/policies`                              | any   | List policies (paginated)  |
| POST   | `/api/v1/policies/{policy_id}/statements`       | admin | Add permission statement   |
| DELETE | `/api/v1/policies/{policy_id}/statements/{sid}` | admin | Remove statement           |

#### Users

| Method | Route                                     | Who   | Description                         |
|--------|-------------------------------------------|-------|-------------------------------------|
| GET    | `/api/v1/users`                           | any   | List users in org (paginated)       |
| GET    | `/api/v1/users/{user_id}`                 | any   | Get user details                    |
| POST   | `/api/v1/users/{user_id}/groups`          | admin | Add user to group                   |
| DELETE | `/api/v1/users/{user_id}/groups/{grp_id}` | admin | Remove user from group              |
| GET    | `/api/v1/users/{user_id}/groups`          | any   | List groups for a user              |
| GET    | `/api/v1/users/{user_id}/policies`        | any   | Resolve full effective permissions  |

---

## Invite Flow

How a new user joins an existing org (a fresh signup always creates a new org):

```
Admin                                        Invitee
─────────────────────────────────────────    ─────────────────────────────────
POST /api/v1/orgs/{id}/invites               Receives invite_token out-of-band
{ email, group_id }                          (copy-paste from admin dashboard)
        │
        ▼
Returns: { invite_token, expires_at }        POST /api/v1/auth/accept-invite
                                             { invite_token, password }
                                                     │
                                                     ▼
                                             User created in same org
                                             Placed in invited group
                                             Invitation deleted (one-time use)
                                             Returns: { access_token, refresh_token }
                                             → auto-logged in, lands on /dashboard
```

- `invite_token` — 256-bit random string, stored in `invitations` table, expires in 7 days
- Not a JWT — looked up by value in DB, deleted on use (single-use)
- Admin generates via dashboard (`/dashboard/invites`), shares the token manually

---

## Platform Hardening (Phase 4)

### Redis Rate Limiting (Gateway)

Every protected route enforces **1000 requests per org per 60 seconds**.

- Key: `ratelimit:{org_id}` — one counter per organization, not per user
- INCR + EXPIRE sent as a single pipeline (one Redis round-trip)
- Exceeding the limit: `429 Too Many Requests` with `error_code: RATE_LIMIT_EXCEEDED`
- Redis down: **fail-open** — request is allowed, warning logged

### Policy Cache (User-Service)

`GET /api/v1/users/{id}/policies` is cached in Redis to avoid repeated DB joins.

- Key: `policy:{user_id}` | TTL: 300 seconds
- Cache hit: returns immediately with `from_cache: true`
- Invalidation: cache key deleted whenever user is added to or removed from a group
- Redis down: falls through to DB query, no error returned

### Structured JSON Logging (All Services)

Every request is logged as one JSON line:

```json
{
  "timestamp":   "2026-05-24T08:15:00.123Z",
  "service":     "gateway",
  "level":       "INFO",
  "message":     "request",
  "method":      "POST",
  "path":        "/api/v1/auth/login",
  "status":      200,
  "duration_ms": 45,
  "request_id":  "3f2a1b4c-8d2e-4f1a-b3c9-7e1d5f9a2c8b"
}
```

The gateway generates a UUID `request_id` per request and forwards it as `x-request-id` to all downstream services. All three services log the same `request_id` for one client request — grep by it to trace a request end-to-end.

### Alembic Migrations (Auth-Service)

All schema changes are versioned and tracked. `alembic upgrade head` runs at every auth-service startup.

```bash
# Verify migration applied
docker exec agentwork_postgres psql -U admin -d agentwork -c "SELECT * FROM alembic_version;"
# → 0001

# List all tables
docker exec agentwork_postgres psql -U admin -d agentwork -c "\dt"
# → 11 rows (10 data tables + alembic_version)
```

---

## Response Field Names

All response schemas use named ID fields (never the generic `id`):

| Resource  | Field name in response |
|-----------|------------------------|
| User      | `user_id`              |
| Group     | `group_id`             |
| Policy    | `policy_id`            |
| Statement | `statement_id`         |
| Org       | `org_id`               |
| Invite    | `invite_token`         |

---

## Standard Error Response

All services return errors in this format:

```json
{
  "error_code": "TOKEN_INVALID",
  "message":    "Invalid email or password",
  "request_id": "3f2a1b4c-8d2e-4f1a-b3c9-7e1d5f9a2c8b",
  "timestamp":  "2026-05-24T10:30:00.000000+00:00"
}
```

| Status | `error_code`          | When                                           |
|--------|-----------------------|------------------------------------------------|
| 400    | `INVITE_ERROR`        | Invalid, expired, or already-used invite token |
| 400    | `VALIDATION_ERROR`    | Missing or invalid request fields              |
| 401    | `TOKEN_EXPIRED`       | Access token past its 2-hour life              |
| 401    | `TOKEN_INVALID`       | Malformed, wrong signature, or revoked         |
| 401    | `TOKEN_MISSING`       | No `Authorization` header sent                 |
| 403    | `ACCESS_DENIED`       | Non-admin calling an admin-only route          |
| 404    | `NOT_FOUND`           | Resource does not exist in this org            |
| 409    | `CONFLICT`            | Duplicate record (email, org name, etc.)       |
| 429    | `RATE_LIMIT_EXCEEDED` | Org exceeded 1000 requests per 60 seconds      |
| 503    | `SERVICE_UNAVAILABLE` | Downstream service unreachable                 |

---

## Identity Headers (Gateway → Services)

The gateway injects these headers on every forwarded request (public and protected):

| Header          | Value                                         | Set from        |
|-----------------|-----------------------------------------------|-----------------|
| `x-user-email`  | `alice@acme.com`                              | JWT `sub` claim |
| `x-org-id`      | `550e8400-...`                                | JWT `org_id`    |
| `x-user-groups` | `admin,support`                               | JWT `groups`    |
| `x-request-id`  | `3f2a1b4c-8d2e-4f1a-b3c9-7e1d5f9a2c8b`       | Gateway UUID    |

On public routes (auth endpoints), `x-user-email`, `x-org-id`, and `x-user-groups` are not set — only `x-request-id` is always forwarded.

---

## Implementation Phases

| Phase | Goal                                                                       | Status      |
|-------|----------------------------------------------------------------------------|-------------|
| 1     | Core auth — signup, login, refresh, logout, JWT issuance                   | **Done**    |
| 2     | PBAC — orgs, groups, policies, user-group management, identity headers     | **Done**    |
| 3     | Invite flow — admin invites members into an org + group                    | **Done**    |
| 4     | Platform hardening — rate limiting, policy cache, JSON logging, Alembic    | **Done**    |
| 5     | Service registry — dynamic gateway routing from DB                         | Not started |
| 6     | Frontend — Next.js admin dashboard                                         | **Done**    |
| 7     | Solution integration — connect first AI solution, solution launcher UI     | Not started |

> Phase 5 (service registry) and Phase 7 (solution launcher) are the next two milestones. Phase 5 builds the `/registry/register` API and dynamic gateway routing. Phase 7 connects the first AI solution and adds a solution picker to the frontend.

---

## Architecture Documentation

Step-by-step build notes in [architecture_steps_info/project-setup/](architecture_steps_info/project-setup/):

| File | Covers |
|------|--------|
| `0.DB_postgres_infra.md` | PostgreSQL setup, all 10 tables, init.sql |
| `2.docker_compose.md` | Docker Compose config — all services explained |
| `3.Auth_service.md` + `3a` + `3b` | Auth service reference, testing, concepts |
| `4.gateway-service.md` + `4a` + `4b` | Gateway reference, testing, concepts |
| `5.user-service.md` + `5a` + `5b` | User service reference, testing, concepts |
| `6.invite-flow.md` + `6a` + `6b` | Invite flow reference, testing, concepts |
| `7.platform-hardening.md` + `7a` + `7b` | Rate limiting, policy cache, JSON logging, Alembic |
| `PBAC-understanding.md` | Deep dive: PBAC vs RBAC, permission chain, token lifecycle |

---

## Adding a Solution Microservice

Solution services run in separate repos. To connect to the platform (Phase 5+):

1. Join the `agentwork-platform` Docker network
2. Call `POST /registry/register` at startup (Phase 5 API — not yet built)
3. Expose `GET /health`
4. Read identity from headers the gateway injects on every request:

| Header          | Contains                                    |
|-----------------|---------------------------------------------|
| `x-user-email`  | Authenticated user's email                  |
| `x-org-id`      | The user's organization UUID                |
| `x-user-groups` | Comma-separated list of the user's groups   |
| `x-request-id`  | Unique request ID for cross-service tracing |

5. Scope all data queries to `x-org-id` to maintain tenant isolation

---

## Local Development — Useful Commands

```bash
# Database inspection
docker exec agentwork_postgres psql -U admin -d agentwork -c "\dt"
docker exec agentwork_postgres psql -U admin -d agentwork -c "SELECT * FROM alembic_version;"

# Redis inspection
docker exec -it agentwork_redis redis-cli
> KEYS ratelimit:*          # rate limit counters
> KEYS policy:*             # policy cache entries
> GET ratelimit:<org_id>    # current request count for an org

# Live log tailing
docker compose logs -f gateway
docker compose logs -f auth-service
docker compose logs -f user-service

# Find all logs for one request across services
docker compose logs | grep "<request_id>"

# Rebuild a single service without restarting others
docker compose up --build --no-deps auth-service
```

## DBeaver Connection (Local Dev)

| Field    | Value       |
|----------|-------------|
| Host     | `localhost` |
| Port     | `5432`      |
| Database | `agentwork` |
| Username | `admin`     |
| Password | `admin`     |

Navigate to `agentwork → Schemas → public → Tables` to inspect all 10 tables.
