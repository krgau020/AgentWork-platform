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

Invite flow (Phase 3):
  POST /api/v1/orgs/{org_id}/invites — admin creates a one-time invite token
  for a specific email + group. The token is returned in the response.
  The invitee submits the token to auth-service POST /api/v1/auth/accept-invite.
  This route uses header_org_id (from x-org-id, set by gateway from JWT) as the
  authoritative org scope — the path org_id is structural only.

Policy update flow (feature/policy-management):
  PUT /api/v1/policies/{id}                        — rename a policy
  PUT /api/v1/policies/{id}/statements/{sid}       — edit a statement in place
  Both are admin-only and org-scoped. statement_id is preserved on update so
  existing group assignments that reference the statement are not disrupted.

Service registry (feature/service-registry):
  POST   /api/v1/registry/register             — admin registers a solution
  GET    /api/v1/registry/services             — list active solutions (any auth user)
  DELETE /api/v1/registry/services/{id}        — admin removes a solution
  GET    /internal/registry/{name}             — gateway-only lookup: name → base_url + route_prefix
                                                 No JWT required; reachable only on internal Docker network.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.cache import get_policy_cache, invalidate_policy_cache, set_policy_cache
from app.db.session import get_db
from app.schemas.organization import OrgResponse
from app.schemas.group import GroupCreate, GroupResponse, PolicyAssign
from app.schemas.invite import InviteCreate, InviteResponse
from app.schemas.policy import PolicyCreate, PolicyUpdate, PolicyResponse, StatementCreate, StatementUpdate, StatementResponse
from app.schemas.user import UserResponse, GroupAssign, UserPoliciesResponse
from app.schemas.registry import ServiceRegisterRequest, ServiceResponse
from app.services import org_service, group_service, invite_service, policy_service, user_service, registry_service
from app.models.service_registry import ServiceRegistry

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


@router.post("/api/v1/orgs/{org_id}/invites", response_model=InviteResponse)
def create_invite(
    org_id: UUID,
    body: InviteCreate,
    db: Session = Depends(get_db),
    header_org_id: UUID = Depends(get_org_id),
    _: str = Depends(require_admin),
):
    """
    Create a one-time invite token for a new user.

    The path org_id is for RESTful URL structure. header_org_id (from x-org-id,
    set by the gateway from the admin's JWT) is used as the authoritative org scope
    so an admin cannot create invites for a different organization.

    Returns the invite_token the admin must share with the invitee out-of-band.
    """
    return invite_service.create_invite(db, header_org_id, body.email, body.group_id)


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
    result = group_service.list_groups(db, org_id, page, limit)
    result["data"] = [GroupResponse.model_validate(g).model_dump() for g in result["data"]]
    return result


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
    result = policy_service.list_policies(db, org_id, page, limit)
    result["data"] = [PolicyResponse.model_validate(p).model_dump() for p in result["data"]]
    return result


@router.put("/api/v1/policies/{policy_id}", response_model=PolicyResponse)
def update_policy(
    policy_id: UUID,
    body: PolicyUpdate,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
    _: str = Depends(require_admin),
):
    return policy_service.update_policy(db, policy_id, body.name, org_id)


@router.post("/api/v1/policies/{policy_id}/statements", response_model=StatementResponse)
def add_statement(
    policy_id: UUID,
    body: StatementCreate,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
    _: str = Depends(require_admin),
):
    return policy_service.add_statement(db, policy_id, body.resource, body.action, body.effect, org_id)


@router.put("/api/v1/policies/{policy_id}/statements/{statement_id}", response_model=StatementResponse)
def update_statement(
    policy_id: UUID,
    statement_id: UUID,
    body: StatementUpdate,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
    _: str = Depends(require_admin),
):
    return policy_service.update_statement(db, policy_id, statement_id, body.resource, body.action, body.effect, org_id)


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
    result = user_service.list_users(db, org_id, page, limit)
    result["data"] = [UserResponse.model_validate(u).model_dump() for u in result["data"]]
    return result


@router.get("/api/v1/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
):
    return user_service.get_user(db, user_id, org_id)


@router.post("/api/v1/users/{user_id}/groups")
async def add_user_to_group(
    user_id: UUID,
    body: GroupAssign,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
    _: str = Depends(require_admin),
):
    group_service.add_user_to_group(db, user_id, body.group_id, org_id)
    await invalidate_policy_cache(str(user_id))
    return {"message": "User added to group"}


@router.delete("/api/v1/users/{user_id}/groups/{group_id}")
async def remove_user_from_group(
    user_id: UUID,
    group_id: UUID,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
    _: str = Depends(require_admin),
):
    group_service.remove_user_from_group(db, user_id, group_id, org_id)
    await invalidate_policy_cache(str(user_id))
    return {"message": "User removed from group"}


@router.get("/api/v1/users/{user_id}/groups")
def get_user_groups(
    user_id: UUID,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
):
    groups = user_service.get_user_groups(db, user_id, org_id)
    return [GroupResponse.model_validate(g).model_dump() for g in groups]


@router.get("/api/v1/users/{user_id}/policies")
async def get_user_policies(
    user_id: UUID,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
):
    cached = await get_policy_cache(str(user_id))
    if cached is not None:
        return {"user_id": str(user_id), "policies": cached, "from_cache": True}
    policies = user_service.get_user_policies(db, user_id, org_id)
    await set_policy_cache(str(user_id), policies)
    return {"user_id": str(user_id), "policies": policies, "from_cache": False}


# ─────────────────────────────────────────────────────────────────────────────
# Service Registry
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/api/v1/registry/register", response_model=ServiceResponse)
def register_service(
    body: ServiceRegisterRequest,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin),
):
    return registry_service.register_service(
        db, body.name, body.display_name, body.base_url,
        body.route_prefix, body.allowed_groups, body.health_endpoint,
    )


@router.get("/api/v1/registry/services")
def list_services(
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
):
    services = registry_service.list_services(db)
    return [ServiceResponse.model_validate(s).model_dump() for s in services]


@router.delete("/api/v1/registry/services/{service_id}")
def deregister_service(
    service_id: UUID,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin),
):
    registry_service.deregister_service(db, service_id)
    return {"message": "Service deregistered"}


# ─────────────────────────────────────────────────────────────────────────────
# Internal Registry Lookup — gateway only, no JWT required
#
# The gateway calls this directly on the internal Docker network to resolve
# a service name → base_url + route_prefix before forwarding chat requests.
# Not exposed through the gateway's public routing — only reachable on :8003.
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/internal/registry/{name}")
def get_service_internal(name: str, db: Session = Depends(get_db)):
    service = (
        db.query(ServiceRegistry)
        .filter(ServiceRegistry.name == name, ServiceRegistry.is_active == True)
        .first()
    )
    if not service:
        raise HTTPException(
            status_code=404,
            detail={"error_code": "NOT_FOUND", "message": f"Service '{name}' not found"},
        )
    return {"base_url": service.base_url, "route_prefix": service.route_prefix}
