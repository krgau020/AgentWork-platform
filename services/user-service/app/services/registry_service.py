"""
Registry Service (app/services/registry_service.py)

Business logic for the service registry — the platform's directory of
registered AI solution microservices.

Admin actions:
  register_service   — add a new solution to the registry; 409 if name taken
  deregister_service — permanently remove a solution by service_id

Read actions:
  list_services      — all active services (for frontend solution list)
  get_service_by_name — look up a single service; used by the gateway at
                        route time to resolve name → base_url + route_prefix

Unlike groups/policies, service_registry is NOT org-scoped. Solutions are
platform-level — every org sees every registered solution (access is
controlled by allowed_groups + PBAC, not by org_id filtering).
"""

import uuid
from uuid import UUID
from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.service_registry import ServiceRegistry


def register_service(
    db: Session,
    name: str,
    display_name: str,
    base_url: str,
    route_prefix: str,
    allowed_groups: List[str],
    health_endpoint: str,
) -> ServiceRegistry:
    existing = db.query(ServiceRegistry).filter(ServiceRegistry.name == name).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail={"error_code": "CONFLICT", "message": f"Service '{name}' is already registered"},
        )
    service = ServiceRegistry(
        id=uuid.uuid4(),
        name=name,
        display_name=display_name,
        base_url=base_url,
        route_prefix=route_prefix,
        allowed_groups=allowed_groups,
        health_endpoint=health_endpoint,
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


def list_services(db: Session) -> List[ServiceRegistry]:
    return db.query(ServiceRegistry).filter(ServiceRegistry.is_active == True).all()


def get_service_by_name(db: Session, name: str) -> ServiceRegistry:
    service = (
        db.query(ServiceRegistry)
        .filter(ServiceRegistry.name == name, ServiceRegistry.is_active == True)
        .first()
    )
    if not service:
        raise HTTPException(
            status_code=404,
            detail={"error_code": "NOT_FOUND", "message": f"Service '{name}' not found or inactive"},
        )
    return service


def deregister_service(db: Session, service_id: UUID) -> None:
    service = db.query(ServiceRegistry).filter(ServiceRegistry.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=404,
            detail={"error_code": "NOT_FOUND", "message": "Service not found"},
        )
    db.delete(service)
    db.commit()
