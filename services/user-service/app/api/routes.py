"""
User-Service Routes (app/api/routes.py)

All requests arrive here after the gateway has:
  1. Validated the JWT
  2. Injected identity headers

This service reads those headers — it never sees the JWT itself.

Identity headers (set by gateway, trusted):
  x-user-email:  who is making this request
  x-org-id:      which tenant — ALL DB queries filter by this
  x-user-groups: comma-separated groups — used for admin checks

Admin check:
  Write operations (POST, DELETE) require x-user-groups to contain "admin".
  Read operations (GET) are allowed for any authenticated user.
  require_admin() enforces this — if not admin, raises 403.

Multi-tenancy:
  Every query includes .filter(...org_id == org_id).
  A user from org A can never see org B's data even if they
  guess the UUID of org B's resource.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.organization import OrgResponse
from app.schemas.group import GroupCreate, GroupResponse, PolicyAssign
from app.schemas.policy import PolicyCreate, PolicyResponse, StatementCreate, StatementResponse
from app.schemas.user import UserResponse, GroupAssign, UserPoliciesResponse
from app.services import org_service, group_service, policy_service, user_service

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Identity helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_org_id(x_org_id: str = Header(...)) -> UUID:
    try:
        return UUID(x_org_id)
    except ValueError:
        raise HTTPException(status_code=400, detail={"error_code": "VALIDATION_ERROR", "message": "Invalid org_id header"})


def require_admin(x_user_groups: str = Header(...)):
    groups = [g.strip() for g in x_user_groups.split(",")]
    if "admin" not in groups:
        raise HTTPException(status_code=403, detail={"error_code": "ACCESS_DENIED", "message": "Admin access required"})


# ─────────────────────────────────────────────────────────────────────────────
# Organizations
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/api/v1/orgs/{org_id}", response_model=OrgResponse)
def get_org(
    org_id: UUID,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin),
):
    return org_service.get_org(db, org_id)


# ─────────────────────────────────────────────────────────────────────────────
# Groups
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/api/v1/groups", response_model=GroupResponse)
def create_group(
    body: GroupCreate,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
    _: str = Depends(require_admin),
):
    return group_service.create_group(db, body.name, org_id)


@router.get("/api/v1/groups")
def list_groups(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
):
    return group_service.list_groups(db, org_id, page, limit)


@router.post("/api/v1/groups/{group_id}/policies")
def assign_policy_to_group(
    group_id: UUID,
    body: PolicyAssign,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
    _: str = Depends(require_admin),
):
    group_service.assign_policy(db, group_id, body.policy_id, org_id)
    return {"message": "Policy assigned to group"}


@router.delete("/api/v1/groups/{group_id}/policies/{policy_id}")
def remove_policy_from_group(
    group_id: UUID,
    policy_id: UUID,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
    _: str = Depends(require_admin),
):
    group_service.remove_policy(db, group_id, policy_id, org_id)
    return {"message": "Policy removed from group"}


# ─────────────────────────────────────────────────────────────────────────────
# Policies
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/api/v1/policies", response_model=PolicyResponse)
def create_policy(
    body: PolicyCreate,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
    _: str = Depends(require_admin),
):
    return policy_service.create_policy(db, body.name, org_id)


@router.get("/api/v1/policies")
def list_policies(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
):
    return policy_service.list_policies(db, org_id, page, limit)


@router.post("/api/v1/policies/{policy_id}/statements", response_model=StatementResponse)
def add_statement(
    policy_id: UUID,
    body: StatementCreate,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
    _: str = Depends(require_admin),
):
    return policy_service.add_statement(db, policy_id, body.resource, body.action, body.effect, org_id)


@router.delete("/api/v1/policies/{policy_id}/statements/{statement_id}")
def remove_statement(
    policy_id: UUID,
    statement_id: UUID,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
    _: str = Depends(require_admin),
):
    policy_service.remove_statement(db, policy_id, statement_id, org_id)
    return {"message": "Statement removed"}


# ─────────────────────────────────────────────────────────────────────────────
# Users
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/api/v1/users")
def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
):
    return user_service.list_users(db, org_id, page, limit)


@router.get("/api/v1/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
):
    return user_service.get_user(db, user_id, org_id)


@router.post("/api/v1/users/{user_id}/groups")
def add_user_to_group(
    user_id: UUID,
    body: GroupAssign,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
    _: str = Depends(require_admin),
):
    group_service.add_user_to_group(db, user_id, body.group_id, org_id)
    return {"message": "User added to group"}


@router.delete("/api/v1/users/{user_id}/groups/{group_id}")
def remove_user_from_group(
    user_id: UUID,
    group_id: UUID,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
    _: str = Depends(require_admin),
):
    group_service.remove_user_from_group(db, user_id, group_id, org_id)
    return {"message": "User removed from group"}


@router.get("/api/v1/users/{user_id}/groups")
def get_user_groups(
    user_id: UUID,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
):
    return user_service.get_user_groups(db, user_id, org_id)


@router.get("/api/v1/users/{user_id}/policies")
def get_user_policies(
    user_id: UUID,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
):
    policies = user_service.get_user_policies(db, user_id, org_id)
    return {"user_id": str(user_id), "policies": policies}
