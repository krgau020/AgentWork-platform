"""
Registry Schemas (app/schemas/registry.py)

Pydantic models for the service registry API.

Classes:

    ServiceRegisterRequest — request body for POST /api/v1/registry/register
        Admin provides: name (slug), display_name, base_url, route_prefix,
        allowed_groups, health_endpoint.
        name must be URL-safe (used in /api/v1/solutions/{name}/chat).
        base_url is the internal Docker URL (e.g. http://chatbot:8004).
        route_prefix is the path appended for chat calls (default /chat).
        allowed_groups controls who can use the service:
          ["*"]         — any authenticated user
          ["admin"]     — admin group only
          ["admin","eng"] — either group

    ServiceResponse — returned by register + list endpoints
        Includes all stored fields plus service_id.
        is_active lets the frontend hide deactivated services.
        base_url is intentionally exposed so admins can verify the URL.
"""

from pydantic import BaseModel, Field
from uuid import UUID
from typing import List, Optional
from datetime import datetime


class ServiceRegisterRequest(BaseModel):
    name: str
    display_name: str
    base_url: str
    route_prefix: str = "/chat"
    allowed_groups: List[str] = ["*"]
    health_endpoint: str = "/health"


class ServiceResponse(BaseModel):
    service_id: UUID = Field(validation_alias="id")
    name: str
    display_name: Optional[str]
    base_url: str
    route_prefix: str
    allowed_groups: List[str]
    health_endpoint: str
    is_active: bool
    registered_at: Optional[datetime]

    model_config = {"from_attributes": True}
