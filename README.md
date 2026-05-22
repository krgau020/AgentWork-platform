# AgentWork Platform

Multi-tenant SaaS infrastructure for AI-powered solutions. The platform handles authentication, authorization, request routing, and policy-based access control. Solution microservices plug in via the service registry — no platform code change needed to add a new service.

---

## Platform Architecture

```
                        ┌─────────────────────┐
                        │   Client / Browser   │
                        └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────┐
                        │   API Gateway :8000  │  JWT validation, routing,
                        │                      │  CORS, request tracing
                        └──┬───────────────┬───┘
                           │               │
              ┌────────────▼───┐    ┌──────▼─────────┐
              │  Auth Service  │    │  User Service   │
              │    :8001       │    │    :8003        │
              │                │    │                 │
              │ signup / login │    │ orgs / groups / │
              │ refresh/logout │    │ policies / users│
              │ accept-invite  │    │ invitations     │
              └────────┬───────┘    └──────┬──────────┘
                       │                   │
              ┌────────▼───────────────────▼──────────┐
              │          PostgreSQL :5432              │
              │          Redis :6379                   │
              └───────────────────────────────────────┘
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

| Service      | Port | Container                | Responsibility                                      | Status       |
|--------------|------|--------------------------|-----------------------------------------------------|--------------|
| API Gateway  | 8000 | `agentwork_gateway`      | JWT validation, routing, CORS, tracing              | **Complete** |
| Auth Service | 8001 | `agentwork_auth_service` | Signup, login, refresh, logout, accept-invite       | **Complete** |
| User Service | 8003 | `agentwork_user_service` | Orgs, groups, policies, user management, invites    | **Complete** |
| Frontend     | 3000 | `agentwork_frontend`     | Next.js admin UI                                    | Not started  |

## Infrastructure

| Service    | Port | Container            | Purpose                                      |
|------------|------|----------------------|----------------------------------------------|
| PostgreSQL | 5432 | `agentwork_postgres` | Platform database — 10 tables                |
| Redis      | 6379 | `agentwork_redis`    | Cache / session store (Phase 4)              |

> PostgreSQL and Redis are internal. Do not call them directly from solution services.

---

## Database Schema — 10 Tables

```
organizations       → root tenant boundary — one row per company
users               → platform users, each scoped to one org
tokens              → active refresh tokens (server-side revocation)
groups              → named collections of users within an org
policies            → named permission sets within an org
policy_statements   → individual rules: resource + action + allow/deny
group_policies      → which policies a group has (join table)
user_groups         → which groups a user belongs to (join table)
invitations         → one-time invite tokens for adding users to an org (Phase 3)
service_registry    → registered solution microservices and routing config
```

Schema is defined in `infra/postgres/init.sql` and runs automatically on first PostgreSQL container start.

> **Note:** If you add a table, run `docker compose down -v && docker compose up --build` to recreate the volume and apply the new schema.

---

## Quick Start

```bash
# Build and start all platform services
docker compose up --build

# View live logs for a service
docker compose logs -f auth-service

# Rebuild one service after code changes
docker compose up --build user-service

# Stop all services
docker compose down

# Stop and wipe all data (resets the database — runs init.sql again on next start)
docker compose down -v
```

After startup, verify:
```
GET http://localhost:8000/health  →  {"status": "ok", "service": "gateway"}
GET http://localhost:8001/health  →  {"status": "ok", "service": "auth-service"}
GET http://localhost:8003/health  →  {"status": "ok", "service": "user-service"}
```

---

## Complete API Reference

All routes go through the gateway at port **8000**. The gateway validates JWT and forwards to the correct service.

### Auth Routes — Public (no JWT required)

Full documentation: [services/auth-service/README.md](services/auth-service/README.md)

| Method | Route                          | Description                                              |
|--------|--------------------------------|----------------------------------------------------------|
| POST   | `/api/v1/auth/signup`          | Create user + org + default admin group                  |
| POST   | `/api/v1/auth/login`           | Returns `access_token` (2h) + `refresh_token` (7d)      |
| POST   | `/api/v1/auth/refresh`         | Token rotation — old token revoked, new pair issued      |
| POST   | `/api/v1/auth/logout`          | Revokes refresh token                                    |
| POST   | `/api/v1/auth/accept-invite`   | Accept invite token, create account, return token pair   |

**JWT payload issued on login / accept-invite:**
```json
{
  "sub": "alice@acme.com",
  "org_id": "550e8400-e29b-41d4-a716-446655440000",
  "groups": ["admin"],
  "exp": 1748000000
}
```

---

### User-Service Routes — Protected (JWT required)

Full documentation: [services/user-service/README.md](services/user-service/README.md)

The gateway validates the JWT and injects identity headers before forwarding here. All routes are scoped to the caller's `org_id` — cross-org access is impossible.

#### Organizations

| Method | Route                        | Who Can Call | Description                              |
|--------|------------------------------|--------------|------------------------------------------|
| GET    | `/api/v1/orgs/{org_id}`      | admin        | Get org details                          |
| POST   | `/api/v1/orgs/{org_id}/invites` | admin     | Create one-time invite token             |

#### Groups

| Method | Route                                       | Who Can Call | Description                    |
|--------|---------------------------------------------|--------------|--------------------------------|
| POST   | `/api/v1/groups`                            | admin        | Create group                   |
| GET    | `/api/v1/groups`                            | any          | List groups (paginated)        |
| POST   | `/api/v1/groups/{group_id}/policies`        | admin        | Assign policy to group         |
| DELETE | `/api/v1/groups/{group_id}/policies/{p_id}` | admin        | Remove policy from group       |

#### Policies

| Method | Route                                              | Who Can Call | Description               |
|--------|----------------------------------------------------|--------------|---------------------------|
| POST   | `/api/v1/policies`                                 | admin        | Create policy             |
| GET    | `/api/v1/policies`                                 | any          | List policies (paginated) |
| POST   | `/api/v1/policies/{policy_id}/statements`          | admin        | Add permission statement  |
| DELETE | `/api/v1/policies/{policy_id}/statements/{sid}`    | admin        | Remove statement          |

#### Users

| Method | Route                                     | Who Can Call | Description                          |
|--------|-------------------------------------------|--------------|--------------------------------------|
| GET    | `/api/v1/users`                           | any          | List users in org (paginated)        |
| GET    | `/api/v1/users/{user_id}`                 | any          | Get user details                     |
| POST   | `/api/v1/users/{user_id}/groups`          | admin        | Add user to group                    |
| DELETE | `/api/v1/users/{user_id}/groups/{grp_id}` | admin        | Remove user from group               |
| GET    | `/api/v1/users/{user_id}/groups`          | any          | List groups for a user               |
| GET    | `/api/v1/users/{user_id}/policies`        | any          | Resolve full effective permissions   |

**"any"** = any authenticated user (valid JWT).  
**"admin"** = x-user-groups header must contain "admin" (set by gateway from JWT).

---

## Invite Flow (Phase 3)

How a second user joins an existing org (they can't signup — that creates a new org):

```
Admin                                    Invitee
─────────────────────────────────────    ─────────────────────────────────────
POST /api/v1/orgs/{id}/invites           Receives invite_token out-of-band
{ email, group_id }
        │
        ▼
Returns: { invite_token, expires_at }    POST /api/v1/auth/accept-invite
                                         { invite_token, password }
                                                 │
                                                 ▼
                                         New user created in org
                                         Placed in invited group
                                         Invitation deleted (one-time use)
                                         Returns: { access_token, refresh_token }
```

The `invite_token` is a 256-bit random string stored in the `invitations` table. It is not a JWT — it is looked up by value in the DB and deleted on use. It expires in 7 days.

Full documentation: [architecture_steps_info/project-setup/6.invite-flow.md](architecture_steps_info/project-setup/6.invite-flow.md)

---

## Response ID Field Names

All response schemas use specific named IDs (not generic `id`):

| Resource | Field name in response |
|----------|------------------------|
| User     | `user_id`              |
| Group    | `group_id`             |
| Policy   | `policy_id`            |
| Statement| `statement_id`         |
| Org      | `org_id`               |
| Invite   | `invite_token`         |

---

## Standard Error Response

All services return errors in this format:

```json
{
  "error_code": "TOKEN_INVALID",
  "message": "Invalid email or password",
  "request_id": "3f2a1b4c-8d2e-4f1a-b3c9-7e1d5f9a2c8b",
  "timestamp": "2026-05-21T10:30:00.000000+00:00"
}
```

| Status | error_code          | When                                   |
|--------|---------------------|----------------------------------------|
| 400    | INVITE_ERROR        | Invalid, expired, or already-used invite token |
| 400    | VALIDATION_ERROR    | Missing or invalid request fields      |
| 401    | TOKEN_EXPIRED       | Access token past expiry               |
| 401    | TOKEN_INVALID       | Malformed, wrong signature, or revoked |
| 401    | TOKEN_MISSING       | No Authorization header                |
| 403    | ACCESS_DENIED       | Non-admin calling an admin-only route  |
| 404    | NOT_FOUND           | Resource does not exist in this org    |
| 409    | CONFLICT            | Duplicate record                       |
| 503    | SERVICE_UNAVAILABLE | Downstream service unreachable         |

---

## Implementation Phases

| Phase | Goal                                                         | Status           |
|-------|--------------------------------------------------------------|------------------|
| 1     | Core auth — signup, login, refresh, logout, JWT              | **Done**         |
| 2     | PBAC — orgs, groups, policies, user-group management         | **Done**         |
| 3     | Invite flow — admin invites users into an org + group        | **Done**         |
| 4     | Platform hardening — Redis rate limiting, policy cache, logs | Not started      |
| 5     | Service registry — dynamic gateway routing from DB           | Not started      |
| 6     | Frontend — Next.js admin UI                                  | Not started      |
| 7     | First solution integration                                   | Not started      |

---

## Architecture Documentation

Step-by-step build notes live in [architecture_steps_info/project-setup/](architecture_steps_info/project-setup/):

| File | Covers |
|------|--------|
| `0.DB_postgres_infra.md` | PostgreSQL setup, all 10 tables, init.sql |
| `2.docker_compose.md` | Docker Compose config explanation |
| `3.Auth_service.md` + `3a` + `3b` | Auth service reference, testing, concepts |
| `4.gateway-service.md` + `4a` + `4b` | Gateway reference, testing, concepts |
| `5.user-service.md` + `5a` + `5b` | User service reference, testing, concepts |
| `6.invite-flow.md` + `6a` + `6b` | Invite flow reference, testing, concepts |
| `PBAC-understanding.md` | Deep dive: PBAC vs RBAC, permission model |

---

## Adding a Solution Microservice

Solution services run in separate repos. To connect to the platform:

1. Join the `agentwork-platform` Docker network
2. Call `POST /registry/register` on startup (Phase 5)
3. Expose `GET /health`
4. Read identity from headers injected by the gateway:

| Header          | Contains                                   |
|-----------------|--------------------------------------------|
| `x-user-email`  | Authenticated user's email                 |
| `x-org-id`      | The user's organization UUID               |
| `x-user-groups` | Comma-separated list of the user's groups  |
| `x-request-id`  | Unique request ID for cross-service tracing|

5. Scope all data queries to `x-org-id` to maintain tenant isolation

---

## DBeaver Connection (Local Dev)

| Field    | Value       |
|----------|-------------|
| Host     | `localhost` |
| Port     | `5432`      |
| Database | `agentwork` |
| Username | `admin`     |
| Password | `admin`     |

Navigate to `agentwork → Schemas → public → Tables` to inspect all 10 tables.
