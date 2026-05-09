# Validation Service

Data validation and business rules service.

**Port:** 8005

## Responsibility

- Data validation
- Business rule enforcement
- Input sanitization
- Compliance checks
- Error validation

## Structure

```
validation-service/
├── app/
│   ├── api/      - Validation endpoints
│   ├── core/     - Validation rules, schemas
│   ├── models/   - Validation schemas
│   ├── services/ - Validation logic
│   └── main.py   - FastAPI app
├── Dockerfile
├── requirements.txt
└── .env
```

## Entry Point

`app/main.py` - Starts FastAPI server on port 8005

## Purpose

Centralized validation service to ensure data quality across all services.
