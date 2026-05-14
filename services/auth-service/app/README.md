# app/

Main application code for the auth service.

See the full documentation in [`../../README.md`](../../README.md).

## Subdirectories

- `api/` — HTTP route handlers for /signup, /login, /refresh.
- `core/` — Configuration loading and security utilities (hashing, JWT).
- `db/` — SQLAlchemy base, engine, and session factory.
- `models/` — Database table definitions (users, tokens).
- `schemas/` — Pydantic request/response validation schemas.
- `services/` — Business logic. No HTTP concerns here.
- `main.py` — FastAPI app bootstrap. Start here.
