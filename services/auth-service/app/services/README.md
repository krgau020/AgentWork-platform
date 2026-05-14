# services/

Business logic layer. No HTTP concerns here.

See the full documentation in [`../../../README.md`](../../../README.md).

## Files

- `auth_service.py` — `create_user`, `login_user`, `refresh_access_token`. Called by routes, talks to DB and security utils.
