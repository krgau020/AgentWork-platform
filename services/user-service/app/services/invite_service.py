"""
Invite Service (app/services/invite_service.py)

Business logic for creating organization invitations. This is the user-service
side of the Phase 3 invite flow. The auth-service side (accepting the invite)
lives in auth-service/app/services/auth_service.py.

What this service does:
    create_invite() validates the target group, generates a secure random token,
    sets a 7-day expiry, and saves the invitation row to the DB. It returns the
    Invitation ORM object so the route can serialize it into an InviteResponse.

What this service does NOT do:
    - Does NOT send emails. Phase 3 returns the token in the API response;
      the admin shares it manually. Email delivery is a Phase 4+ concern.
    - Does NOT create the user. That happens in auth-service when the invitee
      accepts the invite with POST /api/v1/auth/accept-invite.

Security design:
    Token is generated with secrets.token_urlsafe(32) — 256 bits of entropy.
    It is NOT a JWT (no expiry in the token itself). Expiry is enforced by
    comparing expires_at from the DB row against the current time at accept.
    One-time use is enforced by deleting the row on acceptance.

    Group ownership is validated: invite_service checks that the group_id belongs
    to org_id before saving. This prevents an admin from inviting someone to a
    group in a different organization (even if they know the UUID).

Dependencies:
    - app.models.invitation  →  Invitation ORM model
    - app.models.group       →  Group ORM model (for group ownership validation)
    - Used by: app.api.routes (POST /api/v1/orgs/{org_id}/invites)
"""

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.group import Group
from app.models.invitation import Invitation


def create_invite(db: Session, org_id: UUID, email: str, group_id: UUID) -> Invitation:
    """
    Create a one-time invitation for a new user to join an org and group.

    Validates that the target group belongs to the caller's org, then generates
    a secure token valid for 7 days. The token is stored in the invitations table
    and returned to the caller (admin) to share with the invitee.

    Args:
        db:       Active database session.
        org_id:   The organization UUID (from the x-org-id header — trusted).
        email:    The invitee's email address (informational; uniqueness is
                  validated by auth-service at accept time, not here).
        group_id: The group the invitee will be placed into after acceptance.

    Returns:
        Invitation ORM object with token and expires_at populated.

    Raises:
        HTTPException 404: If group_id does not exist within org_id.
    """
    group = db.query(Group).filter(Group.id == group_id, Group.org_id == org_id).first()
    if not group:
        raise HTTPException(
            status_code=404,
            detail={"error_code": "NOT_FOUND", "message": "Group not found in your organization"}
        )

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    invite = Invitation(
        org_id=org_id,
        email=str(email),
        group_id=group_id,
        token=token,
        expires_at=expires_at,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite
