"""
Organization Schemas (app/schemas/organization.py)

Pydantic models that define the API shape for organization-related responses.

Why schemas are separate from ORM models:
    The Organization ORM model (models/organization.py) describes the DB table.
    This schema describes what the API returns to the client.
    They are intentionally kept separate — the DB shape and the API shape
    can differ without breaking each other.

OrgResponse:
    Returned when a client calls GET /api/v1/orgs/{id}.
    Contains only id and name — nothing internal or sensitive.

    model_config from_attributes=True:
        Tells Pydantic it can read data directly from a SQLAlchemy model object
        (attribute access) instead of requiring a plain dict. Without this,
        FastAPI cannot serialize ORM query results into JSON responses.

What is NOT in this file:
    OrgCreate — organizations are created by auth-service at signup, not by
    user-service. User-service only reads org data. So there is no create schema here.
"""

from pydantic import BaseModel
from uuid import UUID


class OrgResponse(BaseModel):
    id: UUID
    name: str

    model_config = {"from_attributes": True}
