# Gateway Service

Central entry point for all FinSight platform requests. The frontend only knows this service — it routes internally to auth-service, document-service, and others.

**Port:** `8000`
**Base URL (local):** `http://localhost:8000`

---

## What This Service Does

- Validates JWT tokens on every protected request (centralized auth)
- Routes requests to the correct downstream service
- Propagates user identity (email, role) via internal headers
- Stamps every request with a unique request_id for tracing
- Handles CORS for browser-based frontend access
- Returns clean 503 errors if a downstream service is down

---

## File Structure

```
gateway/
│
├── app/
│   ├── main.py              Entry point. Creates FastAPI app, registers
│   │                        middleware and CORS, mounts router.
│   │
│   ├── api/
│   │   ├── __init__.py      Marks api/ as a Python package.
│   │   └── routes.py        All route definitions. Forwards requests to
│   │                        downstream services using httpx. Protected routes
│   │                        require JWT via verify_jwt_token dependency.
│   │
│   └── core/
│       ├── __init__.py      Marks core/ as a Python package.
│       ├── config.py        Reads JWT_SECRET_KEY and AUTH_SERVICE_URL
│       │                    from environment variables.
│       ├── security.py      verify_jwt_token — validates Bearer token,
│       │                    returns decoded payload {sub, role, exp}.
│       └── middleware.py    Stamps every request with a UUID request_id
│                            for distributed tracing across services.
│
├── requirements.txt         fastapi, uvicorn, python-jose, httpx, python-dotenv
├── Dockerfile               Builds container. Runs uvicorn with --reload.
└── .env                     JWT_SECRET_KEY, AUTH_SERVICE_URL. Not committed to git.
```

---

## API Endpoints

| Method | Route | Auth | Forwards To | Notes |
|---|---|---|---|---|
| GET | `/health` | No | — | Gateway liveness check |
| POST | `/auth/signup` | No | auth-service:8001 | Create user account |
| POST | `/auth/login` | No | auth-service:8001 | Returns access + refresh tokens |
| POST | `/auth/refresh` | No | auth-service:8001 | Returns new access token |
| GET | `/documents` | Yes | document-service:8002 | Protected — needs Bearer token |

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `JWT_SECRET_KEY` | Yes | Must match `SECRET_KEY` in auth-service |
| `AUTH_SERVICE_URL` | No | Default: `http://auth-service:8001` |

---

## How to Run

**With Docker (recommended):**
```bash
docker compose up -d --build gateway
```

**Locally (for debugging):**
```bash
cd services/gateway
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Check logs:**
```bash
docker compose logs gateway --follow
```

---

## Internal Headers Sent to Services

On protected routes, after JWT validation, gateway forwards:

```
x-user-email:  admin@test.com
x-user-role:   user
x-request-id:  3f2a1b4c-8d2e-4f1a-b3c9-...
```

Downstream services read these headers. They never see the raw JWT.

---

## Error Responses

| Situation | Status | Response |
|---|---|---|
| No Authorization header | 401 | `Missing authorization token` |
| Wrong scheme | 401 | `Invalid auth scheme` |
| Token expired | 401 | `Token expired` |
| Invalid token | 401 | `Invalid token` |
| Downstream service down | 503 | `Auth/Document service unavailable` |
