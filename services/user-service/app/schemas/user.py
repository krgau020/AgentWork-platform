"""
User Schemas (app/schemas/user.py)

Pydantic models for the user management API.
User-service never creates or deletes users — that is auth-service's job.
These schemas are for reading user data and managing group memberships.

Classes:

    UserResponse — returned by GET /api/v1/users and GET /api/v1/users/{id}
        Safe public view of a user record.
        Deliberately excludes password_hash — that column exists in the DB
        but must never be exposed through any API response.
        model_config from_attributes=True lets Pydantic read from SQLAlchemy objects.

    GroupAssign — request body for POST /api/v1/users/{id}/groups
        Used when the admin adds a user to a group.
        Client sends the group_id to assign.
        The user_id comes from the URL path parameter, not the body.
        The org_id comes from the x-org-id header (gateway sets it from JWT).

    UserPoliciesResponse — returned by GET /api/v1/users/{id}/policies
        The result of the full PBAC resolution chain.
        Contains the user_id and a list of all policies they have,
        with each policy's statements expanded.
        Uses List[dict] because the policy resolution result is built
        dynamically in user_service.py, not loaded directly from one table.

Deployment note:
    UserResponse does not include a role field — this platform uses PBAC,
    not RBAC. Permissions come from group memberships and policy statements,
    not from a role column. Role-based thinking would require a separate
    role per user; PBAC composes permissions from groups and reusable policies.
"""

from pydantic import BaseModel
from uuid import UUID
from typing import List


class UserResponse(BaseModel):
    id: UUID
    email: str
    org_id: UUID
    is_active: bool

    model_config = {"from_attributes": True}


class GroupAssign(BaseModel):
    group_id: UUID


class UserPoliciesResponse(BaseModel):
    user_id: UUID
    policies: List[dict]
