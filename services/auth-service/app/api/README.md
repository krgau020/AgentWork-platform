# api/

HTTP route handlers for the auth service.

See the full documentation in [`../../../README.md`](../../../README.md).

## Files

- `routes.py` — POST /signup, /login, /refresh. Validates requests, calls services/auth_service.py, maps errors to HTTP codes.
