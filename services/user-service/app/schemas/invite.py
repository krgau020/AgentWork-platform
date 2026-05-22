"""
Invite Schemas (app/schemas/invite.py)

Pydantic models for the invitation API.

Invite flow:
    Admin (POST /api/v1/orgs/{org_id}/invites) → receives invite_token
    Admin shares token with invitee out-of-band (email, Slack, etc.)
    Invitee (POST /api/v1/auth/accept-invite) → submits token + password → gets JWT pair

Classes:

    InviteCreate — request body for POST /api/v1/orgs/{org_id}/invites
        Admin sends the intended recipient's email and the group they should join.
        org_id comes from the URL path (matches what the gateway set in x-org-id).
        The server assigns: id, token (random), expires_at (now + 7 days), created_at.

    InviteResponse — returned after invite creation
        Returns the invite_token so the admin can share it.
        Also echoes email and org_id back so the admin can confirm the correct target.
        expires_at tells the admin when the token stops working (7 days).

        model_config from_attributes=True lets Pydantic read directly from the
        Invitation SQLAlchemy ORM object without converting to a dict first.

Deployment note:
    The invite_token is an opaque random string, NOT a JWT. It is stored in the
    invitations table and looked up by exact value when the invitee accepts.
    This design makes one-time invalidation trivial — the row is deleted on accept.
    No email delivery is done in Phase 3; the admin receives the token via API response.
"""

from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime


class InviteCreate(BaseModel):
    email: EmailStr
    group_id: UUID


class InviteResponse(BaseModel):
    invite_token: str = Field(validation_alias="token")
    email: str
    org_id: UUID
    expires_at: datetime

    model_config = {"from_attributes": True}
