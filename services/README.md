# Services

All microservices for the FinSight AI Platform.

## Services Structure

Each service follows the same pattern:
```
service-name/
├── app/
│   ├── api/          - API routes & endpoints
│   ├── core/         - Business logic, configs
│   ├── models/       - Database models & schemas
│   ├── services/     - Service layer
│   └── main.py       - FastAPI entry point
├── Dockerfile        - Docker configuration
├── requirements.txt  - Python dependencies
├── .env              - Environment variables
└── README.md         - Service documentation
```

## Services List

| Service | Port | Purpose |
|---------|------|---------|
| Gateway | 8000 | API Gateway, routes requests |
| Auth Service | 8001 | Authentication, JWT tokens |
| Document Service | 8002 | Document upload/storage |
| User Service | 8003 | User management |
| AI Service | 8004 | AI/ML operations |
| Validation Service | 8005 | Data validation |

## Service Port Mapping (Fixed)

```
🚪 Gateway             → 8000
🔐 Auth Service        → 8001
📄 Document Service    → 8002
👤 User Service        → 8003
🤖 AI Service          → 8004
✔️ Validation Service  → 8005
```

## Communication

Services communicate via HTTP/REST and share data through PostgreSQL & Redis.
