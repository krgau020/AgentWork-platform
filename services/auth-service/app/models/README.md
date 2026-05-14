# models/

SQLAlchemy database table definitions.

See the full documentation in [`../../../README.md`](../../../README.md).

## Files

- `user.py` — `users` table: id, email, hashed password, role.
- `token.py` — `tokens` table: id, user_id, refresh_token. Used for session revocation.
