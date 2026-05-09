# Document Service

Document management and storage service.

**Port:** 8002

## Responsibility

- Document upload/download
- Document storage management
- File processing
- Document metadata
- Version control

## Structure

```
document-service/
├── app/
│   ├── api/      - Document endpoints (upload, download, list)
│   ├── core/     - File handling, storage config
│   ├── models/   - Document schemas, database models
│   ├── services/ - Document business logic, file ops
│   └── main.py   - FastAPI app
├── Dockerfile
├── requirements.txt
└── .env
```

## Entry Point

`app/main.py` - Starts FastAPI server on port 8002

## Dependencies

- Auth Service (for permission checks)
- PostgreSQL (for metadata storage)
- File Storage (S3/Local)
