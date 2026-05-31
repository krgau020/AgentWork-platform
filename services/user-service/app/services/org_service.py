"""
Org Service (app/services/org_service.py)

Business logic for reading organization data.

Why read-only:
    Organizations are created by auth-service during signup — one org is created
    atomically with the first user and their admin group. User-service never
    creates or deletes orgs; it only reads them when an admin needs to inspect
    org details via GET /api/v1/orgs/{org_id}.

Multi-tenancy:
    The get_org() function validates the org_id from the URL path against the
    database. The caller (routes.py) already receives the trusted org_id from
    the x-org-id header (set by gateway from JWT), so cross-org access is
    prevented at the gateway layer before this service is ever called.

Dependencies:
    - app.models.organization  →  Organization ORM model
    - Used by: app.api.routes (GET /api/v1/orgs/{org_id})
"""

from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.organization import Organization


def get_org(db: Session, org_id: UUID) -> Organization:
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail={
            "error_code": "NOT_FOUND",
            "message": "Organization not found",
        })
    return org
