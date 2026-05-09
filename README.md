# FinSight AI Platform

## Overview
FinSight AI Platform is a comprehensive financial intelligence system built with microservices architecture.

## Service Port Mapping

| Service | Port |
|---------|------|
| Gateway | 8000 |
| Auth Service | 8001 |
| Document Service | 8002 |
| User Service | 8003 |
| AI Service | 8004 |
| Validation Service | 8005 |

## Getting Started
See documentation for setup and deployment instructions.




## Running Services

### Microservices (Test with Bruno/Browser)

| Service | Port | Status | URL | Type |
|--------|------|--------|-----|------|
| Gateway | 8000 | ✅ Running | http://localhost:8000 | REST API |
| Auth Service | 8001 | ✅ Running | http://localhost:8001 | REST API |
| Document Service | 8002 | ✅ Running | http://localhost:8002 | REST API |
| User Service | 8003 | ✅ Running | http://localhost:8003 | REST API |
| AI Service | 8004 | ✅ Running | http://localhost:8004 | REST API |
| Validation Service | 8005 | ✅ Running | http://localhost:8005 | REST API |

### Infrastructure Services (Internal use only)

| Service | Port | Status | Purpose |
|--------|------|--------|---------|
| PostgreSQL | 5432 | ✅ Running | Database storage |
| Redis | 6379 | ✅ Running | Cache/Session storage |

**Note:** PostgreSQL and Redis are NOT HTTP endpoints. Do NOT test them with Bruno. Microservices use them internally.