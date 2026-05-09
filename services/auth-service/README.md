# Auth Service

Authentication and authorization service.

**Port:** 8001

## Responsibility

- User login/logout
- JWT token generation & validation
- Password hashing & verification
- Session management
- Permission checking

## Structure

```
auth-service/
│
├── app/
│   ├── main.py
│   ├── api/
│   │   └── routes.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   ├── db/
│   │   ├── session.py
│   │   └── base.py   
│   ├── models/
│   │   ├── user.py
│   │   └── token.py
│   ├── schemas/
│   │   └── user.py
│   ├── services/
│   │   └── auth_service.py
│
├── requirements.txt
├── Dockerfile
└── .env
```

## Entry Point

`app/main.py` - Starts FastAPI server on port 8001


## Database

Uses PostgreSQL for user storage via shared config.

## Password Security

- Passwords are hashed with Argon2 (preferred) for new users; legacy bcrypt hashes are still accepted for existing users.
- Passwords must meet strong policy:
  - At least 12 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit
  - At least one special character
  - Maximum 256 characters
- If a password does not meet these requirements, the API returns a clear error message.
- Argon2 is a modern, memory-hard password hashing algorithm recommended for production systems.
- No password truncation is performed (unlike bcrypt's 72-byte limit).

**If you are migrating from bcrypt:**
- Existing users can still log in with their old password (bcrypt hashes are still verified).
- To upgrade, re-hash their password with Argon2 on next login or password change.










## 🐳 3. Dockerfile — Do We Need It at Service Level?


Each microservice must have its own:

Dockerfile
dependencies
runtime
Why?

Because in real systems:

auth-service runs independently
ai-service runs independently
document-service runs independently

👉 Each is its own deployable unit







### Flow understanding


🧠 4. Why Is Auth-Service Running?

You asked:

is it because of internal Dockerfile or root docker?

👉 Answer: BOTH (together)

Flow:
Step 1 → docker-compose.yml
auth-service:
  build: ./services/auth-service

👉 This tells Docker:

“Go to this folder and build it”

Step 2 → Dockerfile inside auth-service

👉 Defines:

Python version
dependencies
how to run app
Step 3 → Docker Compose runs it
docker-compose up

👉 Now container is created → service runs

🧠 Simple Analogy
Dockerfile = recipe
docker-compose = restaurant manager