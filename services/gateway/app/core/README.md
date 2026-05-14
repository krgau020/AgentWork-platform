# core/

Shared utilities used across the gateway.

See the full documentation in [`../../../README.md`](../../../README.md).

## Files

- `config.py` — Reads `JWT_SECRET_KEY` and `AUTH_SERVICE_URL` from environment.
- `security.py` — `verify_jwt_token` dependency. Validates Bearer tokens on protected routes.
- `middleware.py` — Stamps every request with a UUID `request_id` for distributed tracing.
