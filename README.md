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

| Service      | Port | Container                | Responsibility                                 | Status          |
|--------------|------|--------------------------|------------------------------------------------|-----------------|
| API Gateway  | 8000 | `agentwork_gateway`      | JWT validation, routing, CORS, tracing         | In progress     |
| Auth Service | 8001 | `agentwork_auth_service` | Signup, login, refresh, logout, JWT issuance   | **Complete**    |
| User Service | 8003 | `agentwork_user_service` | Orgs, groups, policies, user-group management  | Skeleton only   |
| Frontend     | 3000 | `agentwork_frontend`     | Next.js admin UI                               | Not started     |

## Infrastructure

| Service    | Port | Container            | Purpose                                      |
|------------|------|----------------------|----------------------------------------------|
| PostgreSQL | 5432 | `agentwork_postgres` | Platform database — 9 tables                 |
| Redis      | 6379 | `agentwork_redis`    | Cache / session store (future phases)        |

> PostgreSQL and Redis are internal. Do not call them directly from solution services.

---

## Database Schema — 9 Tables

```
organizations       → root tenant boundary — one row per company
users               → platform users, each scoped to one org
tokens              → active refresh tokens (server-side revocation)
groups              → named collections of users within an org
policies            → named permission sets within an org
policy_statements   → individual rules: resource + action + allow/deny
group_policies      → which policies a group has (join table)
user_groups         → which groups a user belongs to (join table)
service_registry    → registered solution microservices and routing config
```

Schema is defined in `infra/postgres/init.sql` and runs automatically on first PostgreSQL container start.

---

## Quick Start

```bash
# Build and start all platform services (except frontend)
docker compose up --build

# Start including the frontend
docker compose --profile frontend up --build

# View live logs for a service
docker compose logs -f auth-service

# Rebuild one service after code changes
docker compose up --build auth-service

# Apply docker-compose.yml config changes (force full recreation)
docker compose up --force-recreate auth-service

# Open a shell inside a running container
docker exec -it agentwork_auth_service bash

# Stop all services
docker compose down

# Stop and wipe all data (resets the database)
docker compose down -v
```

After startup, verify:
```
GET http://localhost:8001/health  →  {"status": "ok", "service": "auth-service"}
```

---

## Auth Service API — Complete

Full documentation: [services/auth-service/README.md](services/auth-service/README.md)

| Method | Route                     | Auth | Description                                         |
|--------|---------------------------|------|-----------------------------------------------------|
| POST   | `/api/v1/auth/signup`     | No   | Create user + org + default admin group             |
| POST   | `/api/v1/auth/login`      | No   | Returns `access_token` (2h) + `refresh_token` (7d) |
| POST   | `/api/v1/auth/refresh`    | No   | Token rotation — old token revoked, new pair issued |
| POST   | `/api/v1/auth/logout`     | No   | Revokes refresh token                               |
| GET    | `/health`                 | No   | Service health check                                |

**JWT payload issued on login:**
```json
{
  "sub": "alice@acme.com",
  "org_id": "550e8400-e29b-41d4-a716-446655440000",
  "groups": ["admin"],
  "exp": 1748000000
}
```

---

## Planned API — Future Phases

### User Service (Phase 2)

| Method | Route                                   | Auth  | Description                        |
|--------|-----------------------------------------|-------|------------------------------------|
| POST   | `/api/v1/orgs`                          | admin | Create organization                |
| GET    | `/api/v1/orgs/{id}`                     | admin | Get org details                    |
| POST   | `/api/v1/groups`                        | admin | Create group in org                |
| GET    | `/api/v1/groups`                        | admin | List groups (paginated)            |
| POST   | `/api/v1/groups/{id}/policies`          | admin | Assign policy to group             |
| DELETE | `/api/v1/groups/{id}/policies/{p_id}`   | admin | Remove policy from group           |
| POST   | `/api/v1/policies`                      | admin | Create a named policy              |
| GET    | `/api/v1/policies`                      | admin | List policies (paginated)          |
| POST   | `/api/v1/policies/{id}/statements`      | admin | Add permission statement           |
| GET    | `/api/v1/users`                         | admin | List users in org (paginated)      |
| POST   | `/api/v1/users/{id}/groups`             | admin | Add user to group                  |
| DELETE | `/api/v1/users/{id}/groups/{group_id}`  | admin | Remove user from group             |

### Service Registry (Phase 5)

| Method | Route                     | Auth  | Description                      |
|--------|---------------------------|-------|----------------------------------|
| POST   | `/registry/register`      | admin | Register a solution microservice |
| GET    | `/registry/services`      | admin | List registered services         |
| POST   | `/registry/heartbeat`     | No    | Service liveness signal          |

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
| 400    | VALIDATION_ERROR    | Missing or invalid request fields      |
| 401    | TOKEN_EXPIRED       | Access token past expiry               |
| 401    | TOKEN_INVALID       | Malformed, wrong signature, or revoked |
| 401    | TOKEN_MISSING       | No Authorization header                |
| 403    | ACCESS_DENIED       | Insufficient group permissions         |
| 404    | NOT_FOUND           | Resource does not exist                |
| 409    | CONFLICT            | Duplicate record                       |
| 503    | SERVICE_UNAVAILABLE | Downstream service unreachable         |

---

## Implementation Phases

| Phase | Goal                                                    | Status                                     |
|-------|---------------------------------------------------------|--------------------------------------------|
| 1     | Core auth — signup, login, refresh, logout, JWT         | Done                                       |
| 2     | PBAC — orgs, groups, policies, JWT groups claim         | Auth complete — user-service pending       |
| 3     | Org onboarding — default groups/policies on signup      | Admin group auto-created on signup (done)  |
| 4     | Platform hardening — rate limiting, audit log, caching  | Not started                                |
| 5     | Service registry — dynamic gateway routing from DB      | Not started                                |
| 6     | Frontend — Next.js admin UI                             | Not started                                |
| 7     | First solution integration (Churn Investigator)         | Not started                                |

---

## Adding a Solution Microservice

Solution services run in separate repos. To connect to the platform:

1. Join the `agentwork-platform` Docker network
2. Call `POST /registry/register` on startup (available in Phase 5)
3. Expose `GET /health`
4. Read identity from headers injected by the gateway:

| Header          | Contains                                  |
|-----------------|-------------------------------------------|
| `x-user-email`  | Authenticated user's email                |
| `x-org-id`      | The user's organization UUID              |
| `x-user-groups` | Comma-separated list of the user's groups |
| `x-request-id`  | Unique request ID for cross-service tracing|

5. Scope all data queries to `x-org-id` to maintain tenant isolation between organizations

---

## DBeaver Connection (Local Dev)

| Field    | Value       |
|----------|-------------|
| Host     | `localhost` |
| Port     | `5432`      |
| Database | `agentwork` |
| Username | `admin`     |
| Password | `admin`     |

Navigate to `agentwork → Schemas → public → Tables` to inspect all 9 tables.
