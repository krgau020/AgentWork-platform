# Auth Service

> **Port:** 8001 | **Base path:** `/api/v1/auth` | **Container:** `agentwork_auth_service`

Handles all authentication for the AgentWork platform. Responsible for user registration (including org creation), credential verification, JWT issuance, token rotation, and session revocation. No other service issues tokens — everything auth-related flows through here.

---

## Table of Contents

1. [How It Fits in the Platform](#1-how-it-fits-in-the-platform)
2. [Folder Structure](#2-folder-structure)
3. [Environment Variables](#3-environment-variables)
4. [Running the Service](#4-running-the-service)
5. [API Reference](#5-api-reference)
6. [Authentication Flows](#6-authentication-flows)
7. [JWT Payload Structure](#7-jwt-payload-structure)
8. [Security Design](#8-security-design)
9. [Database Tables](#9-database-tables)
10. [Testing with Bruno](#10-testing-with-bruno)
11. [Dependencies](#11-dependencies)

---

## 1. How It Fits in the Platform

```
Client (Browser / Bruno)
        │
        ▼
   API Gateway :8000          ← validates JWT on every request
        │
        ▼
   Auth Service :8001         ← YOU ARE HERE
        │
        ▼
   PostgreSQL :5432           ← users, tokens, organizations, groups, user_groups
```

The gateway forwards unauthenticated requests (`/api/v1/auth/*`) directly to this service without JWT validation — because login and signup do not have a token yet. All other routes go through JWT validation at the gateway first.

After a successful login, the access token issued here is what the gateway validates on every subsequent request.

---

## 2. Folder Structure

```
services/auth-service/
│
├── .env                        Environment variables (dev only — not committed to git)
├── Dockerfile                  python:3.11-slim, uvicorn --reload for hot-reload in dev
├── requirements.txt            Python dependencies
│
└── app/
    ├── main.py                 FastAPI app bootstrap, startup DB check, router registration
    │                           Also: GET / (root), GET /health
    │
    ├── api/
    │   └── routes.py           HTTP route handlers — thin layer, no business logic
    │                           POST /signup, /login, /refresh, /logout
    │
    ├── core/
    │   ├── config.py           Reads all environment variables, exposes settings singleton
    │   └── security.py         Argon2 password hashing, JWT create/decode, password policy
    │
    ├── db/
    │   ├── base.py             SQLAlchemy declarative Base (shared by all models)
    │   └── session.py          Engine, SessionLocal, get_db() FastAPI dependency
    │
    ├── models/                 SQLAlchemy ORM models — map Python classes to DB tables
    │   ├── user.py             → users table
    │   ├── token.py            → tokens table (refresh token store)
    │   ├── organization.py     → organizations table
    │   ├── group.py            → groups table
    │   ├── user_group.py       → user_groups join table
    │   └── invitation.py       → invitations table (read + delete on accept)
    │
    ├── schemas/
    │   └── user.py             Pydantic schemas — request/response shape + validation
    │                           UserCreate, UserLogin, TokenResponse, RefreshResponse,
    │                           RefreshTokenRequest, LogoutRequest, AcceptInviteRequest
    │
    └── services/
        └── auth_service.py     All business logic: create_user, login_user,
                                refresh_access_token, logout_user, accept_invite
```

---

## 3. Environment Variables

The `.env` file is loaded locally via `python-dotenv`. In Docker, values come from `docker-compose.yml` (compose values take priority over `.env`).

| Variable                      | Default    | Description                                              |
|-------------------------------|------------|----------------------------------------------------------|
| `POSTGRES_HOST`               | `postgres` | DB host — `postgres` inside Docker, `localhost` locally  |
| `POSTGRES_PORT`               | `5432`     | DB port                                                  |
| `POSTGRES_USER`               | —          | DB username                                              |
| `POSTGRES_PASSWORD`           | —          | DB password                                              |
| `POSTGRES_DB`                 | —          | DB name — must be `agentwork`                            |
| `SECRET_KEY`                  | —          | JWT signing key — rotate immediately if compromised      |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `120`      | Access token TTL (2 hours)                               |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | `7`        | Refresh token TTL (7 days)                               |
| `REDIS_URL`                   | —          | Reserved — future rate limiting and caching              |

> **Production note:** Never commit `.env` to git. Use a secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.) for production deployments.

---

## 4. Running the Service

### With Docker Compose

```bash
# Build and start (postgres starts automatically as a dependency)
docker compose up --build auth-service

# Live logs
docker compose logs -f auth-service

# Apply docker-compose.yml changes (force full container recreation)
docker compose up --force-recreate auth-service
```

The Dockerfile runs uvicorn with `--reload`, so any `.py` file change inside `services/auth-service/` is picked up instantly — no restart needed.

> Note: `--reload` watches Python files only. Changes to `docker-compose.yml` or `Dockerfile` still require a container restart.

### Verify it is running

```
GET http://localhost:8001/
→ {"message": "Auth Service Running"}

GET http://localhost:8001/health
→ {"status": "ok", "service": "auth-service"}
```

---

## 5. API Reference

All endpoints are prefixed with `/api/v1/auth`. All endpoints are public (no JWT required) — the gateway forwards `/api/v1/auth/*` without token validation.

### POST `/api/v1/auth/signup`

Register a new user. Creates an organization, user, default admin group, and group membership atomically (all-or-nothing transaction).

**Request body:**
```json
{
  "email": "alice@acme.com",
  "password": "Secure@123",
  "org_name": "Acme Corp"
}
```

**Success — 200:**
```json
{
  "message": "User created successfully"
}
```

**Error responses:**

| Status | error_code | Reason |
|--------|------------|--------|
| 409    | CONFLICT   | Email already registered |
| 409    | CONFLICT   | Organization name already taken |
| 409    | CONFLICT   | Password does not meet policy |
| 422    | —          | Invalid email format (Pydantic) |

---

### POST `/api/v1/auth/login`

Authenticate a user and receive a token pair.

**Request body:**
```json
{
  "email": "alice@acme.com",
  "password": "Secure@123"
}
```

**Success — 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error responses:**

| Status | error_code    | Reason |
|--------|---------------|--------|
| 401    | TOKEN_INVALID | Wrong email, wrong password, or inactive account |

> The same error is returned for both wrong email and wrong password — this prevents user enumeration.

---

### POST `/api/v1/auth/refresh`

Exchange a refresh token for a new token pair. The submitted token is immediately invalidated (token rotation — one-time use).

**Request body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success — 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error responses:**

| Status | error_code    | Reason |
|--------|---------------|--------|
| 401    | TOKEN_INVALID | Token expired, already used, malformed, or revoked |

---

### POST `/api/v1/auth/logout`

Revoke a refresh token. The token is deleted from the database and cannot be used again.

**Request body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success — 200:**
```json
{
  "message": "Logged out successfully"
}
```

**Error responses:**

| Status | error_code    | Reason |
|--------|---------------|--------|
| 401    | TOKEN_INVALID | Token not found or already revoked |

---

### POST `/api/v1/auth/accept-invite`

Accept an invitation and create a new user account. **No JWT required** — the invitee has no account yet. Security comes from the `invite_token` being a 256-bit random one-time value that expires in 7 days.

On success: the invitation row is deleted (one-time use), the new user account is created, and a token pair is returned so the user is immediately logged in.

**Request body:**
```json
{
  "invite_token": "ud3xMKJYuSsf568QdbZrmvevvVCYeLxNCdJlAn0XeVw",
  "password": "NewUser@1234"
}
```

**Success — 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error responses:**

| Status | error_code   | Reason |
|--------|--------------|--------|
| 400    | INVITE_ERROR | Token not found or already used |
| 400    | INVITE_ERROR | Token has expired (older than 7 days) |
| 400    | INVITE_ERROR | Email already has an account — log in instead |
| 400    | INVITE_ERROR | Password does not meet policy |

---

### Standard Error Response Shape

All errors follow this format:

```json
{
  "error_code": "TOKEN_INVALID",
  "message": "Invalid email or password",
  "request_id": "3f2a1b4c-8d2e-4f1a-b3c9-7e1d5f9a2c8b",
  "timestamp": "2026-05-21T10:30:00.000000+00:00"
}
```

`request_id` is forwarded from the `x-request-id` header set by the gateway — used to trace a request across services in logs.

---

## 6. Authentication Flows

### Signup (Flow A — New Organization)

```
Client: { email, password, org_name }
    │
    ├─ Validate email format (Pydantic EmailStr)
    ├─ Check email uniqueness
    ├─ Derive slug: "Acme Corp" → "acme-corp"
    ├─ Check slug uniqueness
    │
    ├─ INSERT organizations (name, slug)         → flush → org.id
    ├─ Hash password with Argon2
    ├─ INSERT users (email, password, org_id)    → flush → user.id
    ├─ INSERT groups (org_id, name="admin")      → flush → group.id
    ├─ INSERT user_groups (user_id, group_id)
    └─ db.commit()  ← all 4 rows saved atomically

Response: {"message": "User created successfully"}
```

### Login

```
Client: { email, password }
    │
    ├─ Look up user by email
    ├─ Check user.is_active = True
    ├─ verify_password(plain, argon2_hash)
    │
    ├─ Query current groups:
    │    SELECT groups.name FROM groups
    │    JOIN user_groups ON groups.id = user_groups.group_id
    │    WHERE user_groups.user_id = user.id
    │
    ├─ Build JWT payload: { sub, org_id, groups, exp }
    ├─ create_access_token(payload)   → 2h JWT
    ├─ create_refresh_token({sub})    → 7d JWT (minimal payload)
    ├─ INSERT tokens (user_id, refresh_token)
    └─ db.commit()

Response: { access_token, refresh_token }
```

### Refresh (Token Rotation)

```
Client: { refresh_token }
    │
    ├─ Look up token in tokens table   → not found → 401
    ├─ decode_token(jwt)               → expired/invalid → 401
    │
    ├─ DELETE old token row            ← rotation: token is now dead
    ├─ db.commit()
    │
    ├─ Re-query user's current groups  ← picks up membership changes
    ├─ Issue new access_token + new refresh_token
    ├─ INSERT new token row
    └─ db.commit()

Response: { access_token, refresh_token }
```

---

## 7. JWT Payload Structure

### Access Token (2 hours)

```json
{
  "sub": "alice@acme.com",
  "org_id": "550e8400-e29b-41d4-a716-446655440000",
  "groups": ["admin"],
  "exp": 1748000000
}
```

The gateway reads `org_id` and `groups` from this token and injects them as headers into every downstream request:

| Header           | Value               |
|------------------|---------------------|
| `x-user-email`   | `alice@acme.com`    |
| `x-org-id`       | `550e8400-...`      |
| `x-user-groups`  | `["admin"]`         |
| `x-request-id`   | UUID per request    |

### Refresh Token (7 days)

```json
{
  "sub": "alice@acme.com",
  "exp": 1748500000
}
```

Refresh tokens carry only `sub` and `exp`. No authorization claims — used only to obtain new access tokens, never for API access.

---

## 8. Security Design

### Password Hashing — Argon2

All passwords are hashed with Argon2 (winner of the 2015 Password Hashing Competition). It is memory-hard, making it resistant to GPU and ASIC brute-force attacks. bcrypt is kept as a verification fallback for any pre-existing hashes.

**Password policy enforced on every signup:**

| Rule | Requirement |
|------|-------------|
| Minimum length | 8 characters |
| Maximum length | 256 characters (prevents hash-flooding) |
| Uppercase | At least one |
| Lowercase | At least one |
| Digit | At least one |
| Special character | At least one |

### JWT Signing — HS256

JWTs are signed with HMAC-SHA256 using the `SECRET_KEY`. If the key is rotated, all existing tokens are immediately invalidated. All services verifying tokens must share this key.

### Token Rotation

Every `/refresh` call:
1. Deletes the submitted refresh token from the DB immediately
2. Issues a brand new token pair

A stolen refresh token can only be used once — the legitimate user's next refresh rotates it away. Submitting the same token twice fails on the second attempt.

### User Enumeration Prevention

`/login` returns the same `TOKEN_INVALID` error for wrong email, wrong password, and inactive account. An attacker cannot use the API to discover which emails are registered.

---

## 9. Database Tables

The auth service reads and writes these tables (all defined in `infra/postgres/init.sql`):

| Table           | Operations              | Purpose                                               |
|-----------------|-------------------------|-------------------------------------------------------|
| `organizations` | INSERT, SELECT          | Create org on signup, check slug uniqueness           |
| `users`         | INSERT, SELECT          | Create user, look up by email on login / accept-invite|
| `tokens`        | INSERT, SELECT, DELETE  | Store refresh token, rotation, logout/revocation      |
| `groups`        | INSERT, SELECT          | Create default admin group on signup, resolve on login|
| `user_groups`   | INSERT, SELECT          | Assign user to group on signup, resolve groups        |
| `invitations`   | SELECT, DELETE          | Read invite by token, delete after acceptance         |

The auth service does **not** manage `policies`, `policy_statements`, `group_policies`, or `invitations` (INSERT) — those are owned by the user-service.

---

## 10. Testing with Bruno

Create a collection **Auth Service** in Bruno with these requests:

| # | Name | Method | URL |
|---|------|--------|-----|
| 1 | Signup | POST | `http://localhost:8001/api/v1/auth/signup` |
| 2 | Login | POST | `http://localhost:8001/api/v1/auth/login` |
| 3 | Refresh | POST | `http://localhost:8001/api/v1/auth/refresh` |
| 4 | Logout | POST | `http://localhost:8001/api/v1/auth/logout` |

**Signup body:**
```json
{ "email": "alice@acme.com", "password": "Secure@123", "org_name": "Acme Corp" }
```

**Login body:**
```json
{ "email": "alice@acme.com", "password": "Secure@123" }
```

**Refresh / Logout body:**
```json
{ "refresh_token": "<paste from login response>" }
```

**Verify revocation:** After logout, send Refresh again with the same token — should return 401.

**Inspect JWT:** Paste the `access_token` at [jwt.io](https://jwt.io) — confirm payload shows `sub`, `org_id`, `groups`, and `exp`.

**Verify in DBeaver** (`localhost:5432`, db: `agentwork`, user: `admin`, pass: `admin`):
After signup, check `organizations`, `users`, `groups`, and `user_groups` — each should have 1 new row all linked by UUID.

---

## 11. Dependencies

| Package             | Purpose                                              |
|---------------------|------------------------------------------------------|
| `fastapi`           | Web framework                                        |
| `uvicorn`           | ASGI server (runs with `--reload` in dev)            |
| `sqlalchemy`        | ORM for PostgreSQL                                   |
| `psycopg2-binary`   | PostgreSQL driver                                    |
| `passlib[argon2]`   | Argon2 and bcrypt password hashing                   |
| `python-jose`       | JWT creation and validation (HS256)                  |
| `python-dotenv`     | Load `.env` file in local dev                        |
| `email-validator`   | Required by Pydantic's `EmailStr` for email validation|
