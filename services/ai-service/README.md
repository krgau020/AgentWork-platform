# AI Service

AI/Machine Learning operations service.

**Port:** 8004

## Responsibility

- Financial data analysis
- AI predictions/insights
- Model inference
- Data processing for AI
- Report generation

## Structure

```
ai-service/
├── app/
│   ├── api/      - AI endpoints (analyze, predict, reports)
│   ├── core/     - ML model loading, config
│   ├── models/   - Request/Response schemas
│   ├── services/ - AI logic, model inference
│   └── main.py   - FastAPI app
├── Dockerfile
├── requirements.txt
└── .env
```

## Entry Point

`app/main.py` - Starts FastAPI server on port 8004

## Dependencies

- Document Service (for data input)
- PostgreSQL (for storing results)
- ML Libraries (sklearn, tensorflow, etc.)
