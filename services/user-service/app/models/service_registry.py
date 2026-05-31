"""
ServiceRegistry Model (app/models/service_registry.py)

Maps to the service_registry table — the platform's directory of registered
AI solution microservices.

Each row is one solution the admin has plugged in:
  name           — unique slug used in API routes (e.g. "chatbot")
  display_name   — human-readable label shown in the frontend
  base_url       — internal Docker URL of the solution (e.g. http://chatbot:8004)
  route_prefix   — path the gateway appends to base_url for chat calls (/chat)
  allowed_groups — JSONB list of group names that may use this service;
                   ["*"] means any authenticated user
  health_endpoint — path the platform pings to check liveness (/health)
  is_active      — soft toggle; inactive services are hidden from all users
  registered_at  — when the admin registered this service

The gateway reads this table when it receives:
  POST /api/v1/solutions/{name}/chat
  → looks up name → gets base_url + route_prefix → proxies there
"""

import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from app.db.base import Base


class ServiceRegistry(Base):
    __tablename__ = "service_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(255))
    base_url = Column(String(255), nullable=False)
    route_prefix = Column(String(100), nullable=False, default="/chat")
    allowed_groups = Column(JSONB, nullable=False, default=lambda: ["*"])
    health_endpoint = Column(String(100), nullable=False, default="/health")
    is_active = Column(Boolean, nullable=False, default=True)
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    last_heartbeat = Column(DateTime(timezone=True))
