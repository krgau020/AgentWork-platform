Explain -- in short everything

1. What is SaaS and related concept?

Q: What is SaaS?
A: SaaS means Software as a Service. Users open an app in a browser and the platform runs on servers somewhere else. The provider hosts, updates, and scales the product for all customers.

Q: What is IaaS?
A: IaaS means Infrastructure as a Service. It gives you virtual machines, storage, and networking in the cloud. You manage the apps and OS, while the provider manages the hardware.

Q: What is PaaS?
A: PaaS means Platform as a Service. It gives you a ready platform to run apps without managing servers. You only deploy your code and configuration, while the provider manages runtime, scaling, and OS updates.

Q: How do these fit the architecture?
A: FinSight can use:
- IaaS for raw servers and VMs when you want full control of infrastructure.
- PaaS for deploying apps faster with less server management.
- SaaS for the final product that customers use.

Q: Anything else?
A: Yes, there are also:
- FaaS (Function as a Service) for event-driven functions,
- DBaaS (Database as a Service) for managed databases.
These are optional and help simplify specific parts of the stack.

Q: How does this architecture match SaaS?
A: FinSight is a SaaS design because it has:
- a frontend app for users,
- API gateway and backend services hosted centrally,
- shared infrastructure with multi-tenant access.

Q: What is multi-tenant in this system?
A: Multiple organizations use the same platform, but each organization’s data stays separated by tenant controls and RBAC.


2. Authentication and access control

Q: What is JWT authentication?
A: JWT is a token you get after login. It contains user identity and expiry, and services verify it on each request instead of asking for credentials again.

Q: What is RBAC?
A: Role-Based Access Control means users get roles like Admin, Manager, or User. Each role has permissions for certain actions and data.

Q: What is multi-tenant access control?
A: It means every request checks which organization the user belongs to, so one tenant cannot see another tenant’s invoices or data.


3. Cache, Queue, and infra

Q: What is Redis used for?
A: Redis is a fast in-memory store. It is often used for caching results, tracking status, or storing small temporary data.

Q: What are RabbitMQ and Kafka used for?
A: They are message queues. They let services talk asynchronously, so the document upload can finish quickly while AI processing happens later.

Q: What is Docker?
A: Docker packages each service into a container, so the app runs the same way on any machine.

Q: What is Kubernetes?
A: Kubernetes is a system to run and manage many containers across multiple servers. It is useful later when the platform needs scaling and reliability.


4. Deployment phases

Phase 1:
- Use Docker Compose or similar.
- Run on one machine or one server.
- Keep the system simple for initial development.

Phase 2:
- Move to Kubernetes.
- Run services on multiple nodes.
- Add load balancing, scaling, and better fault tolerance.


5. Key concepts in this architecture

Microservices
- Each service is separate and can be changed or scaled independently.

Multi-Tenancy
- One platform serves many organizations with isolated data.

Async Processing
- Long jobs like AI extraction are handled later through queues, not during the user upload request.

AI Isolation
- AI work is in a separate service so it can have its own compute and can be updated without changing core API services.


6. Important design decisions

✅ Why Microservices?
- Good because each part of the system can scale separately.
- Good because each team or service can evolve without breaking others.
- Caution: it is more complex than a single app, so use it when you need the benefits.

✅ Why AI as a separate service?
- AI work is expensive and different from normal web requests.
- Separating it makes it easier to manage models, costs, and compute resources.

✅ Why Queue?
- Without a queue, the upload request would wait for AI processing and the user would wait too long.
- With a queue, the upload returns fast and processing happens in the background.
- Queues also help retries and failures.

✅ Why RBAC early?
- Enterprise customers expect role-based permissions.
- In accounting/finance, access control is important for security and compliance.


7. S3-compatible storage question

Q: Is S3 free?
A: No, Amazon S3 is not free in production. It is a paid cloud storage service.

Q: What does "S3-compatible" mean?
A: It means the storage service speaks the same API as Amazon S3. You can use AWS S3, or other services like MinIO, Wasabi, or on-premise storage that supports the same interface.

Q: Can I use free storage for development?
A: Yes. For local development, use free S3-compatible tools like MinIO or LocalStack. But for real production, cloud storage usually costs money.










1. Observability (logging / monitoring / tracing)

Without this:

You can’t debug failures
You can’t scale
You can’t operate production
2. Service Contracts & Versioning

Without this:

Microservices break each other
Frontend/backend mismatch happens
3. Security (deep level)

Right now you have basic auth — not enterprise-grade isolation.

4. Backup & Disaster Recovery

Without this:

One DB failure = product dead
5. Document vs Storage Boundary

Right now it’s blurry → leads to tight coupling.













## Future change 

What still needs to be strong for real enterprise readiness
implementation details matter a lot
need CI/CD and deployment automation
need network/security design (service mesh, WAF, VPN/VPC controls)
need compliance controls for finance/GST data
need operational planning for scaling, DR, and incident response
need clear data lifecycle, retention, and backup validation