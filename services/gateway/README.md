# Gateway Service

Single entry point for all external traffic on the AgentWork platform. Every request from a browser, mobile app, or Bruno passes through here. No client talks directly to auth-service or user-service.

Full architecture context: [architecture_steps_info/project-setup/4.gateway-service.md](../../architecture_steps_info/project-setup/4.gateway-service.md)

---

## What It Does

Four responsibilities — nothing else:

1. **Validate JWT** on every protected request
2. **Extract identity** from the token (email, org_id, groups)
3. **Forward identity as headers** to downstream services
4. **Return the downstream response** to the client

No business logic. No database. Just a smart traffic director that checks your ID at the door.

---

## Folder Structure

```
services/gateway/
│
├── .env                        Environment variables (dev only)
├── Dockerfile                  python:3.11-slim, uvicorn --reload
├── requirements.txt            Python dependencies
│
└── app/
    ├── main.py                 FastAPI app bootstrap, CORS, middleware, exception handler
    │
    ├── api/
    │   └── routes.py           All route handlers — public (auth) and protected (user-service)
    │
    └── core/
        ├── config.py           Reads env vars via Pydantic BaseSettings
        ├── middleware.py       Stamps every request with a UUID (request_id)
        └── security.py        JWT validation — get_token_payload() Depends function
```

No `db/`, `models/`, or `schemas/` — the gateway has no database and no business logic.

---

## Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `SECRET_KEY` | `supersecret` | JWT verification key — must match auth-service exactly |
| `ALGORITHM` | `HS256` | JWT algorithm — must match auth-service |
| `AUTH_SERVICE_URL` | `http://auth-service:8001` | Internal Docker URL for auth-service |
| `USER_SERVICE_URL` | `http://user-service:8003` | Internal Docker URL for user-service |

---

## Running

```bash
# Start gateway only
docker compose up --build gateway

# Start all services
docker compose up --build

# Live logs
docker compose logs -f gateway

# Rebuild after requirements.txt change
docker compose up --build gateway
```

Code changes in `app/` are picked up automatically via `--reload` + volume mount. No rebuild needed for Python changes.

---

## API Routes

### Public (no token required)

| Method | Route | Forwards To |
|--------|-------|-------------|
| GET | `/health` | Gateway answers directly |
| POST | `/api/v1/auth/signup` | auth-service:8001 |
| POST | `/api/v1/auth/login` | auth-service:8001 |
| POST | `/api/v1/auth/refresh` | auth-service:8001 |
| POST | `/api/v1/auth/logout` | auth-service:8001 |

### Protected (JWT required)

All routes below require `Authorization: Bearer <access_token>` header.
Gateway validates the token, adds identity headers, forwards to user-service.

| Method | Route | Forwards To |
|--------|-------|-------------|
| GET / POST | `/api/v1/orgs` | user-service:8003 |
| GET / POST / DELETE | `/api/v1/orgs/{path}` | user-service:8003 |
| GET / POST | `/api/v1/users` | user-service:8003 |
| GET / POST / DELETE | `/api/v1/users/{path}` | user-service:8003 |
| GET / POST | `/api/v1/groups` | user-service:8003 |
| GET / POST / DELETE | `/api/v1/groups/{path}` | user-service:8003 |
| GET / POST | `/api/v1/policies` | user-service:8003 |
| GET / POST / DELETE | `/api/v1/policies/{path}` | user-service:8003 |

---

## Identity Headers (added to every protected forward)

```
x-user-email:   alice@acme.com
x-org-id:       550e8400-e29b-41d4-a716-446655440000
x-user-groups:  admin
x-request-id:   3f2a1b4c-8d2e-4f1a-b3c9-7e1d5f9a2c8b
```

Downstream services read these headers — they never decode JWTs.

---

## Error Response Format

All errors from the gateway follow this shape:

```json
{
  "error_code": "TOKEN_INVALID",
  "message": "Invalid or malformed token",
  "request_id": "3f2a1b4c-8d2e-4f1a-b3c9-7e1d5f9a2c8b",
  "timestamp": "2026-05-21T14:24:37.540075+00:00"
}
```

| Status | error_code | When |
|--------|-----------|------|
| 401 | `TOKEN_MISSING` | No Authorization header or not Bearer scheme |
| 401 | `TOKEN_EXPIRED` | Access token past its 2-hour expiry |
| 401 | `TOKEN_INVALID` | Malformed, tampered, or wrong secret key |
| 503 | `SERVICE_UNAVAILABLE` | Downstream service is not reachable |
| 504 | `GATEWAY_TIMEOUT` | Downstream service took too long to respond |

---

## Request Flow

```
Client (Browser / Bruno)
    │
    │  POST /api/v1/auth/login  { email, password }
    ▼
Gateway :8000
    │  No JWT check (public route)
    │  httpx.post(auth-service:8001/api/v1/auth/login)
    ▼
Auth Service :8001
    │  Verifies password, issues tokens
    ▼
Gateway returns { access_token, refresh_token } to client

─────────────────────────────────────────────────────────

Client
    │
    │  GET /api/v1/users
    │  Authorization: Bearer eyJhbGci...
    ▼
Gateway :8000
    │  1. verify_jwt_token() → valid payload
    │  2. Add headers:
    │       x-user-email:  alice@acme.com
    │       x-org-id:      550e8400-...
    │       x-user-groups: admin
    │       x-request-id:  abc-123-xyz
    │  3. httpx.get(user-service:8003/api/v1/users)
    ▼
User Service :8003
    │  Reads x-org-id, queries only that tenant's data
    ▼
Gateway returns response to client
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi` | Web framework |
| `uvicorn[standard]` | ASGI server |
| `pydantic-settings` | Config from .env |
| `python-jose[cryptography]` | JWT decode and verification |
| `httpx` | Async HTTP client for forwarding requests |
| `python-dotenv` | .env file loading |
