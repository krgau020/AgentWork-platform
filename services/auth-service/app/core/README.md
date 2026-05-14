# core/

Shared utilities for configuration and security.

See the full documentation in [`../../../README.md`](../../../README.md).

## Files

- `config.py` — Reads SECRET_KEY, DATABASE_URL, token expiry from env vars. Single settings instance used everywhere.
- `security.py` — Password hashing (Argon2 + bcrypt fallback), password policy validation, JWT create/decode functions.
