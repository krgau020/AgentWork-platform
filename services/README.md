# services/

All microservices for the AgentWork platform.

---

## Current Services

| Service | Port | Status | Purpose |
|---------|------|--------|---------|
| [gateway](gateway/) | 8000 | Planned | API entry point — JWT validation, routing |
| [auth-service](auth-service/) | 8001 | Built | Signup, login, token issuance and rotation |
| [user-service](user-service/) | 8003 | Planned | Orgs, groups, policies, user assignments |

Frontend (Next.js, port 3000) lives in `frontend/` at the project root — started via `--profile frontend`.

---

## Folder Pattern

Every service follows the same structure:

```
service-name/
├── app/
│   ├── api/          — HTTP route handlers (thin layer, no business logic)
│   ├── core/         — Config, security utilities
│   ├── db/           — SQLAlchemy engine, session, Base
│   ├── models/       — ORM models (one file per table)
│   ├── schemas/      — Pydantic request/response schemas
│   ├── services/     — Business logic
│   └── main.py       — FastAPI app, startup, health endpoint
├── Dockerfile
├── requirements.txt
├── .env              — Local dev env vars (not committed)
└── README.md         — Service documentation
```

---

## Service Communication

All services share the `agentwork-platform` Docker network. They reach each other by service name:

```
Client (Browser / Bruno)
    │
    └─→ gateway:8000
            ├─→ auth-service:8001
            └─→ user-service:8003
```

Each service connects to the shared Postgres instance at `postgres:5432` (database: `agentwork`).

---

## Adding a New Service

1. Create the folder under `services/your-service/` following the pattern above
2. Add it to `docker-compose.yml` with the next available port
3. Register it in `service_registry` table so the gateway can route to it
