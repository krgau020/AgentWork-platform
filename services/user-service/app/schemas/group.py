"""
Group Schemas (app/schemas/group.py)

Pydantic models for the group management API.
Groups are named collections of users within one org.
Policies are attached to groups, not directly to users.

Classes:

    GroupCreate — request body for POST /api/v1/groups
        Client sends only the name. The server sets id and org_id.
        org_id comes from the x-org-id header (set by gateway from JWT).
        The client never sends org_id directly.

    GroupResponse — returned by POST /api/v1/groups and GET /api/v1/groups
        Full group record: id, name, org_id.
        model_config from_attributes=True lets Pydantic read from SQLAlchemy objects.

    PolicyAssign — request body for POST /api/v1/groups/{id}/policies
        Used when the admin assigns an existing policy to a group.
        Client sends the policy_id they want to link.
        The group_id comes from the URL path parameter, not the body.

Deployment note:
    All group operations are org-scoped. The service layer always filters
    by org_id from the gateway header — a group created in org A is never
    visible to org B even if they share the same group name.
"""

from pydantic import BaseModel, Field
from uuid import UUID


class GroupCreate(BaseModel):
    name: str


class GroupResponse(BaseModel):
    group_id: UUID = Field(validation_alias="id")
    name: str
    org_id: UUID

    model_config = {"from_attributes": True}


class PolicyAssign(BaseModel):
    policy_id: UUID
