# User Service

User management service.

**Port:** 8003

## Responsibility

- User profile management
- User data CRUD operations
- User preferences
- User roles & permissions
- User profile updates

## Structure

```
user-service/
├── app/
│   ├── api/      - User endpoints (CRUD operations)
│   ├── core/     - Configuration, auth checks
│   ├── models/   - User schemas, database models
│   ├── services/ - User business logic
│   └── main.py   - FastAPI app
├── Dockerfile
├── requirements.txt
└── .env
```

## Entry Point

`app/main.py` - Starts FastAPI server on port 8003

## Dependencies

- Auth Service (for user validation)
- PostgreSQL (for user data storage)
