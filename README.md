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






## Docker command

# Build all services
docker compose build

# Run all services
docker compose up

# Run all services in background
docker compose up -d

# Build one service
docker compose build auth-service

# Run one service
docker compose up auth-service

# Rebuild and run one service
docker compose up --build auth-service

# View logs for one service
docker compose logs -f auth-service

# Stop all services
docker compose down

# Stop and remove volumes
docker compose down -v

# Open terminal inside container
docker exec -it auth-service bash

# If bash does not work
docker exec -it auth-service sh