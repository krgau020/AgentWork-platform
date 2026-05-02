# FinSight AI Platform – Architecture Document (v2)

## 1. Overview

FinSight AI is a microservices-based SaaS platform for processing and validating financial documents using AI.

Initial focus:

* GST Invoice Processing (India)

Future:

* Full financial automation platform

---

## 2. Core Design Principles

* Microservices-based architecture
* API-first design
* Multi-tenant isolation
* Async processing via queue
* AI workload isolation
* Observability-first system
* Failure-tolerant design

---

## 3. High-Level Architecture

Frontend → API Gateway → Services → Queue → AI → Validation → DB → UI

---

## 4. System Components

### API Gateway

* Entry point for all requests
* JWT validation
* Rate limiting
* Request routing

### Auth Service

* Token issuance (JWT)
* RBAC management
* Role definitions

### User & Organization Service

* Multi-tenant user management
* Org-based access control

### Document Service

* Document metadata management
* Processing lifecycle tracking
* Ownership (org/user)
* Idempotency enforcement

### Storage Service

* File upload & retrieval
* Returns file_url
* Storage abstraction layer

### AI Processing Service

* OCR + LLM pipeline
* Converts documents to structured JSON

### Validation Service

* GST validation rules
* Duplicate detection
* Anomaly detection

### Notification Service (Future)

* Email/webhook alerts

---

## 5. Data Flow (Corrected)

1. User uploads invoice via frontend
2. API Gateway validates JWT
3. Request goes to Document Service
4. Document Service calls Storage Service → gets file_url
5. Metadata stored with status = uploaded
6. Status updated → queued
7. Processing event sent to Message Queue
8. AI Processing Service consumes job
9. Status → processing
10. AI extracts structured data
11. Pass to Validation Service
12. Status → validated
13. Results stored in DB
14. Status → completed
15. UI fetches results

---

## 6. Document Lifecycle (Critical)

uploaded
→ queued
→ processing
→ validated
→ completed
→ failed

---

## 7. Failure Handling & Retry Strategy

If AI processing fails:

* Retry up to 3 times
* Use exponential backoff
* If still failing:

  * Mark status = failed
  * Log detailed error
  * Store failure reason
  * Trigger notification (future)

---

## 8. Idempotency Design

To prevent duplicate processing:

* Generate file hash (SHA256)
* Check if document already exists
* Use idempotency key per request

If duplicate:

* Skip reprocessing
* Return existing result

---

## 9. Observability

### Logging

* Structured logs (JSON)
* Include:

  * request_id
  * user_id
  * org_id
  * service_name
  * error

### Monitoring

* CPU / memory
* latency
* error rate
* queue lag

Tools:

* Prometheus + Grafana

### Tracing

* Distributed tracing across services

Tools:

* OpenTelemetry + Jaeger

---

## 10. Security

### Auth Flow

Frontend → API Gateway (JWT validation) → Services

### Multi-Tenant Isolation

* All queries filtered by org_id

### Encryption

* TLS (in transit)
* encrypted storage (at rest)

### Secrets

* Env vars (initial)
* Vault / Secret Manager (future)

---

## 11. Service Communication

* REST (initial)
* gRPC (future)

### API Versioning

* /api/v1/*
* /api/v2/*

No breaking changes allowed.

---

## 12. Infrastructure

* Docker (all services)
* Docker Compose (initial)
* Kubernetes (future)

### Data Layer

* PostgreSQL (primary DB)
* Redis (cache + queue support)

### Messaging

* RabbitMQ / Kafka

---

## 13. Clear Service Boundaries

### Document Service

* metadata
* lifecycle
* idempotency
* ownership

### Storage Service

* file upload
* file retrieval
* returns file_url

---

## 14. Backup & Disaster Recovery

* Daily DB backups
* Backup stored separately
* Restore strategy defined

Future:

* DB replication
* multi-zone deployment

---

## 15. Flow Diagram

```
            [ Frontend (Next.js) ]
                     |
                     v
            [ API Gateway ]
             (JWT Validation)
                     |
                     v
             [ Document Service ]
                |        |
                |        v
                |   [ Storage Service ]
                |        |
                |   (file_url)
                |
                v
          [ Message Queue ]
                |
                v
      [ AI Processing Service ]
                |
                v
         [ Validation Service ]
                |
                v
          [ PostgreSQL DB ]
                |
                v
            [ Frontend UI ]

     [ Redis ]
```

[ Logging | Monitoring | Tracing ]

---

## 16. Development Phases

### Phase 1

* Document upload
* AI extraction
* GST validation

### Phase 2

* Auth + RBAC
* Multi-tenancy

### Phase 3

* Queue + async processing

### Phase 4

* Observability

### Phase 5

* Kubernetes deployment

---

## 17. Future Scope

* Bank statement parsing
* Invoice reconciliation
* Purchase order matching
* Fraud detection
* ERP integrations
* Analytics dashboard
* API marketplace

---

## 18. Success Criteria

* First 20 paying customers
* Stable processing pipeline
* Scalable system
* Expandable services
