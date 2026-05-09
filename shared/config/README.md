# Config Module

Centralized configuration management for the entire platform.

## Current Content

- `settings.py` - Main settings class using Pydantic

## TODO - To be Added

- [ ] Database configuration (connection pooling, migrations)
- [ ] JWT configuration (token generation, validation)
- [ ] Environment variable parsing (validation, types)

## Usage (Future)

```python
from shared.config import settings

# Access configs
db_url = settings.database.url
jwt_secret = settings.jwt.secret_key
redis_url = settings.redis.url
```

## Notes

Settings uses Pydantic BaseSettings for type-safe configuration with .env file support.
