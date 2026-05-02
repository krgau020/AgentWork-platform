# FinSight AI Platform – Architecture Document

## 1. Overview

FinSight AI is a microservices-based SaaS platform designed to process, validate, and analyze financial documents using AI.

The platform is built for scalability, extensibility, and enterprise-level use cases.

Initial focus:

* GST Invoice Processing (India)

Future:

* Full financial automation platform

---

## 🏗️ High-Level Architecture Vision

You will build a system with:

* Independent services
* Scalable infra
* Proper auth
* API gateway
* Async processing
* AI pipeline separation


## 🧱 Infrastructure Components
* Docker (containerization)
* Kubernetes (or start with Docker Compose)
* PostgreSQL (main DB)
* Redis (queue/cache)
* Message Queue (Kafka / RabbitMQ)



## 2. Core Objectives

* Build a production-grade SaaS system
* Enable AI-powered document intelligence
* Support multi-tenant enterprise usage
* Provide scalable microservices architecture

---

## 3. Functional Architecture

### Core Capabilities

1. User Authentication & Authorization
2. Organization & Multi-Tenant Management
3. Document Upload & Storage
4. AI-Based Document Processing
5. Validation Engine (GST Rules)
6. Result Visualization
7. Export & Integration APIs

---

## 4. System Components (Microservices)

### 4.1 API Gateway

* Entry point for all requests
* Handles routing, throttling, auth validation , Rate limiting,Request forwarding

### 4.2 Auth Service

* JWT authentication
* RBAC (Role-Based Access Control)
* Multi-tenant access control

### 4.3 User & Organization Service

* User management
* Organization mapping
* Role assignment

### 4.4 Document Service

* Handles file upload
* Metadata storage
* Status tracking

### 4.5 AI Processing Service

* OCR processing
* LLM-based extraction
* Structured JSON generation

### 4.6 Validation Service

* GST rule engine
* Duplicate detection
* Anomaly detection

### 4.7 Storage Service

* File storage abstraction
* S3-compatible storage   

### 4.8 Notification Service (Future)

* Email alerts
* Webhooks

### 4.9 Frontend Application

* User interface
* Dashboard
* Upload & result visualization

---

## 5. Technical Architecture

### Backend

* FastAPI (Python)

### Frontend

* Next.js (React)

### AI Layer

* OCR + LLM pipeline

### Database

* PostgreSQL

### Cache / Queue

* Redis
* RabbitMQ / Kafka

### Infra

* Docker
* Kubernetes (future)

---

## 6. Data Flow (System Flow)

1. User uploads invoice via UI
2. Request goes through API Gateway
3. Document Service stores file
4. Processing request sent to Queue
5. AI Service processes document
6. Extracted data sent to Validation Service
7. Results stored in DB
8. UI fetches processed results

---

## 7. Flow Diagram

User uploads invoice
   ↓
API Gateway
   ↓
Invoice Service
   ↓
Message Queue
   ↓
AI Processing Service
   ↓
Validation Service
   ↓
Database
   ↓
Frontend shows result

---

## 8. Multi-Tenancy Design

* Each organization has isolated data
* Users belong to organizations
* RBAC ensures secure access

Roles:

* Admin
* Manager
* User

---

## 9. Security Design

* JWT-based authentication
* Role-based access control
* API rate limiting
* Secure file storage
* Input validation

---

## 10. AI Design

AI is isolated in a dedicated service.

Pipeline:

* OCR → Text extraction
* LLM → Structured JSON
* Post-processing

---

## 11. Deployment Architecture

### Phase 1

* Docker Compose
* Single-node deployment

### Phase 2

* Kubernetes cluster
* Service scaling
* Load balancing

---

## 12. Development Phases

### Phase 1 (MVP)

* Document upload
* AI extraction
* GST validation

### Phase 2

* Auth + RBAC
* Multi-tenant system

### Phase 3

* Async processing (queue)
* Scaling services

### Phase 4

* Kubernetes deployment

### Phase 5

* Advanced financial features

---

## 13. Folder Structure (Monorepo)

* /gateway
* /auth-service
* /user-service
* /document-service
* /ai-service
* /validation-service
* /frontend
* /infra

---

## 14. Future Scope

* Bank statement processing
* Invoice reconciliation
* Purchase order matching
* Fraud detection
* Financial analytics dashboard
* Integration with ERP systems
* API marketplace

---

## 15. Design Principles

* Separation of concerns
* Scalability first
* API-first design
* AI isolation
* Async processing

---

## 16. Success Criteria

* First 20 paying customers
* Reliable invoice processing
* Scalable architecture
* Expandable system design







## 17. Observability (Logging, Monitoring, Tracing)

* Logging
  - Structured logging (JSON format)
  - Centralized logging system
  - Use ELK Stack (Elasticsearch, Logstash, Kibana) or Loki + Grafana
  - Each service should log:
    * request_id
    * user_id
    * org_id
    * service_name
    * error details

* Monitoring
  - Track CPU / memory usage
  - Track request latency
  - Track error rates
  - Track queue lag
  - Use Prometheus and Grafana

* Distributed Tracing
  - Track requests across services
  - Example flow: Frontend → Gateway → Invoice → AI → Validation
  - Use Jaeger / OpenTelemetry

## 18. Service Contracts & API Versioning

* API Contracts
  - Each service exposes well-defined APIs
  - Use OpenAPI (Swagger)

* Versioning Strategy
  - Use versions like `/api/v1/invoices` and `/api/v2/invoices`
  - Never break existing APIs; add new versions instead

* Inter-Service Communication
  - REST initially
  - gRPC later for performance

## 19. Advanced Security Design

* Data Isolation (Multi-Tenant)
  - Each request includes `org_id`
  - Users can only access their organization’s data

* Encryption
  - Data in transit: HTTPS / TLS
  - Data at rest: encrypted storage

* Secrets Management
  - Do not store secrets in code
  - Use environment variables initially
  - Use Vault / AWS Secrets Manager later

* API Security
  - Rate limiting
  - Input sanitization
  - JWT validation at the gateway

## 20. Backup & Disaster Recovery

* Backup Strategy
  - Daily database backups
  - Store backups in separate storage

* Recovery Plan
  - Restore DB from backup
  - Reprocess documents if needed

* High Availability (Future)
  - Multi-zone deployment
  - DB replication

## 21. Clear Boundary: Document vs Storage Service

* Document Service handles:
  - metadata
  - status
  - processing state
  - Example fields: `invoice_id`, `file_url`, `status` (uploaded, processing, done)

* Storage Service handles:
  - file upload
  - file retrieval
  - storage abstraction
  - returns `file_url`

* Flow
  - Frontend → Document Service → Storage Service → gets `file_url` → stores metadata

* Document metadata
  - invoice_id
  - file_url
  - status (uploaded, processing, done)

* Storage Service handles:
  - file upload
  - file retrieval
  - storage abstraction
  - returns `file_url`

* Flow
  - Frontend → Document Service → calls Storage Service → gets `file_url` → stores metadata





















##  Flow chart 



                [ Frontend (Next.js) ]
                         |
                         v
                [ API Gateway ]
                         |
                         v
                  [ Auth Service ]
                         |
                         v
                 [ Document Service ]
                    |        |
                    |        v
                    |   [ Storage Service ]
                    |        |
                    |   (returns file_url)
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

         [ Redis (Cache / Queue Support) ]

   [ Logging | Monitoring | Tracing Layer ]