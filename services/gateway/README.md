# Gateway Service

Main API Gateway - entry point for all client requests.

**Port:** 8000

## Responsibility

- Route requests to appropriate microservices
- Authentication/Authorization checks
- Request/Response transformation
- Rate limiting
- Load balancing

## Structure

```
gateway/
├── app/
│   ├── api/      - Gateway routes & endpoints
│   ├── core/     - Configuration, middleware
│   ├── models/   - Request/Response schemas
│   ├── services/ - Business logic
│   └── main.py   - FastAPI app
├── Dockerfile
├── requirements.txt
└── .env
```

## Entry Point

`app/main.py` - Starts FastAPI server on port 8000
