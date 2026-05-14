# Auth Service

Handles all user identity for the FinSight platform. Issues JWT tokens that the gateway uses to authenticate every request across all services.

**Port:** `8001`
**Base URL (local):** `http://localhost:8001`

---

## What This Service Does

- Creates user accounts (signup) with password hashing and policy enforcement
- Authenticates users (login) and issues access + refresh JWT tokens
- Refreshes expired access tokens using a valid refresh token
- Stores refresh tokens in DB to enable revocation
- Assigns and returns user roles (RBAC foundation)

---

## File Structure

```
auth-service/
│
├── app/
│   ├── main.py                 Entry point. Creates FastAPI app, registers routes
│   │                           under /auth prefix. On startup: waits for PostgreSQL,
│   │                           then auto-creates DB tables.
│   │
│   ├── api/
│   │   ├── __init__.py         Marks api/ as a Python package.
│   │   └── routes.py           HTTP route handlers for /signup, /login, /refresh.
│   │                           Validates requests, calls auth_service.py, maps errors
│   │                           to HTTP status codes.
│   │
│   ├── core/
│   │   ├── __init__.py         Marks core/ as a Python package.
│   │   ├── config.py           Reads all env vars: SECRET_KEY, DATABASE_URL,
│   │   │                       token expiry settings. Single settings instance
│   │   │                       used across the service.
│   │   └── security.py         Password hashing (Argon2 + bcrypt fallback),
│   │                           password policy validation, JWT create/decode.
│   │
│   ├── db/
│   │   ├── __init__.py         Marks db/ as a Python package.
│   │   ├── base.py             SQLAlchemy declarative Base. All models inherit
│   │   │                       from this. Used by create_all on startup.
│   │   └── session.py          Creates SQLAlchemy engine and SessionLocal factory.
│   │                           pool_pre_ping prevents stale connection errors.
│   │
│   ├── models/
│   │   ├── __init__.py         Marks models/ as a Python package.
│   │   ├── user.py             users table: id, email, hashed password, role.
│   │   └── token.py            tokens table: id, user_id, refresh_token.
│   │                           Refresh tokens stored here for revocation control.
│   │
│   ├── schemas/
│   │   ├── __init__.py         Marks schemas/ as a Python package.
│   │   └── user.py             Pydantic schemas: UserCreate, UserLogin,
│   │                           TokenResponse, RefreshTokenRequest.
│   │                           FastAPI uses these for automatic request validation.
│   │
│   └── services/
│       ├── __init__.py         Marks services/ as a Python package.
│       └── auth_service.py     All business logic: create_user, login_user,
│                               refresh_access_token. No HTTP concerns here.
│
├── requirements.txt            fastapi, uvicorn, sqlalchemy, psycopg2, passlib,
│                               argon2-cffi, python-jose, python-dotenv
├── Dockerfile                  Builds container. Runs uvicorn with --reload.
└── .env                        Local env vars. Not committed to git.
```

---

## API Endpoints

| Method | Route | Body | Returns |
|---|---|---|---|
| GET | `/` | — | `{"message": "Auth Service Running"}` |
| POST | `/auth/signup` | `{email, password}` | user info (id, email, role) |
| POST | `/auth/login` | `{email, password}` | `{access_token, refresh_token}` |
| POST | `/auth/refresh` | `{refresh_token}` | `{access_token}` |

> In production, all of these are called via the gateway at `localhost:8000`, not directly.

---

## Database Tables

**users**

| Column | Type | Notes |
|---|---|---|
| id | Integer | Primary key |
| email | String | Unique, indexed |
| password | String | Argon2 hash — never plain text |
| role | String | Default `"user"`. Can be `"admin"` |

**tokens**

| Column | Type | Notes |
|---|---|---|
| id | Integer | Primary key |
| user_id | Integer | References user |
| refresh_token | String | Unique. Delete to revoke session |

---

## Token Configuration

| Setting | Env Var | Default |
|---|---|---|
| Access token expiry | `ACCESS_TOKEN_EXPIRE_MINUTES` | 120 min |
| Refresh token expiry | `REFRESH_TOKEN_EXPIRE_DAYS` | 7 days |
| Signing algorithm | hardcoded | HS256 |
| Secret key | `SECRET_KEY` | must be set |

**SECRET_KEY must match JWT_SECRET_KEY in the gateway.** If they differ, gateway rejects all tokens.

---

## Password Policy

Enforced at signup. All rules must pass:

| Rule | Requirement |
|---|---|
| Minimum length | 8 characters |
| Maximum length | 256 characters |
| Uppercase | At least 1 (A-Z) |
| Lowercase | At least 1 (a-z) |
| Digit | At least 1 (0-9) |
| Special character | At least 1 (!@#$% etc.) |

Valid test password: `Admin@1234`

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | JWT signing key. Must match gateway |
| `POSTGRES_HOST` | Yes | DB host (usually `postgres` in Docker) |
| `POSTGRES_PORT` | Yes | DB port (usually `5432`) |
| `POSTGRES_USER` | Yes | DB username |
| `POSTGRES_PASSWORD` | Yes | DB password |
| `POSTGRES_DB` | Yes | Database name |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Default: 120 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | Default: 7 |

---

## How to Run

**With Docker (recommended):**
```bash
docker compose up -d --build auth-service
```

**Locally (for debugging):**
```bash
cd services/auth-service
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**Check logs:**
```bash
docker compose logs auth-service --follow
```

---

## Password Hashing — Argon2 + bcrypt

- **New users** → hashed with Argon2 (modern, memory-hard, recommended)
- **Old users** → bcrypt hashes still verified (migration path)
- passlib's CryptContext handles algorithm selection automatically

If migrating from bcrypt: existing users log in normally. Their hash upgrades to Argon2 on next password change.
