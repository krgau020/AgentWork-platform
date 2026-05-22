"""
Org Service

Fetches org data. Write operations (create org) happen in auth-service at signup.
User-service only reads org data.
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
