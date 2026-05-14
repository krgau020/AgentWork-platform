"""
Auth Service — Pydantic Schemas (app/schemas/user.py)

Purpose:
    Defines request and response data shapes. FastAPI uses these to automatically
    validate incoming JSON, reject malformed requests, and serialize responses.

Schemas:
    UserCreate          — body for POST /auth/signup. Fields: email, password.
    UserLogin           — body for POST /auth/login. Fields: email, password.
                          Separate from UserCreate to allow different validation
                          rules per operation in the future.
    TokenResponse       — response shape for POST /auth/login.
                          Returns both access_token and refresh_token.
    RefreshTokenRequest — body for POST /auth/refresh. Field: refresh_token.
                          Ensures the field name is always "refresh_token" (not "token").

How FastAPI uses these:
    When a route has a Pydantic model as a parameter, FastAPI:
    1. Parses the incoming JSON body.
    2. Validates field types and presence.
    3. Returns 422 Unprocessable Entity automatically if validation fails.
    No manual validation code needed in routes.py.
"""

from pydantic import BaseModel

class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str