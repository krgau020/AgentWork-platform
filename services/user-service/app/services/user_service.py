"""
User Service (app/services/user_service.py)

Business logic for reading user data and resolving permissions.
User-service never creates or deletes users — auth-service owns that.
User-service manages group memberships and resolves effective policies.

Key function: get_user_policies()
  This is the PBAC resolution engine. Given a user_id, it walks the
  full chain:
    user → user_groups → group_policies → policies → policy_statements
  And returns every rule the user has, from all their groups combined.
  This is what a downstream service would call to check if a user
  is allowed to perform a specific action on a specific resource.
"""

from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.user import User
from app.models.group import Group
from app.models.policy import Policy, PolicyStatement
from app.models.group_policy import GroupPolicy
from app.models.user_group import UserGroup


def get_user(db: Session, user_id: UUID, org_id: UUID) -> User:
    user = db.query(User).filter(User.id == user_id, User.org_id == org_id).first()
    if not user:
        raise HTTPException(status_code=404, detail={"error_code": "NOT_FOUND", "message": "User not found"})
    return user


def list_users(db: Session, org_id: UUID, page: int, limit: int) -> dict:
    query = db.query(User).filter(User.org_id == org_id)
    total = query.count()
    users = query.offset((page - 1) * limit).limit(limit).all()
    return {"data": users, "total": total, "page": page, "limit": limit, "pages": -(-total // limit)}


def get_user_groups(db: Session, user_id: UUID, org_id: UUID) -> list:
    user = db.query(User).filter(User.id == user_id, User.org_id == org_id).first()
    if not user:
        raise HTTPException(status_code=404, detail={"error_code": "NOT_FOUND", "message": "User not found"})
    groups = (
        db.query(Group)
        .join(UserGroup, UserGroup.group_id == Group.id)
        .filter(UserGroup.user_id == user_id, Group.org_id == org_id)
        .all()
    )
    return groups


def get_user_policies(db: Session, user_id: UUID, org_id: UUID) -> list:
    """
    Resolve all policies for a user.
    Path: user → user_groups → group_policies → policies → policy_statements
    """
    user = db.query(User).filter(User.id == user_id, User.org_id == org_id).first()
    if not user:
        raise HTTPException(status_code=404, detail={"error_code": "NOT_FOUND", "message": "User not found"})

    group_ids = [ug.group_id for ug in db.query(UserGroup).filter(UserGroup.user_id == user_id).all()]
    policy_ids = [gp.policy_id for gp in db.query(GroupPolicy).filter(GroupPolicy.group_id.in_(group_ids)).all()]

    result = []
    for policy in db.query(Policy).filter(Policy.id.in_(policy_ids), Policy.org_id == org_id).all():
        statements = db.query(PolicyStatement).filter(PolicyStatement.policy_id == policy.id).all()
        result.append({
            "policy_id": str(policy.id),
            "policy_name": policy.name,
            "statements": [
                {"resource": s.resource, "action": s.action, "effect": s.effect}
                for s in statements
            ],
        })
    return result
