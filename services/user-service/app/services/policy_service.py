"""
Policy Service (app/services/policy_service.py)

Business logic for policy and statement management.
All operations are scoped to org_id — a policy from one org
is invisible to another org even if the names match.

Policy lifecycle:
  1. Admin creates a policy (just a name + org_id)
  2. Admin adds statements to it (resource + action + effect rules)
  3. Admin assigns the policy to one or more groups
  4. Users in those groups inherit the policy's statements

Statements can be added and removed individually — you don't need to
rewrite the whole policy to change one rule.
"""

import uuid
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.policy import Policy, PolicyStatement


def create_policy(db: Session, name: str, org_id: UUID) -> Policy:
    existing = db.query(Policy).filter(Policy.name == name, Policy.org_id == org_id).first()
    if existing:
        raise HTTPException(status_code=409, detail={"error_code": "CONFLICT", "message": f"Policy '{name}' already exists"})
    policy = Policy(id=uuid.uuid4(), name=name, org_id=org_id)
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def list_policies(db: Session, org_id: UUID, page: int, limit: int) -> dict:
    query = db.query(Policy).filter(Policy.org_id == org_id)
    total = query.count()
    policies = query.offset((page - 1) * limit).limit(limit).all()
    return {"data": policies, "total": total, "page": page, "limit": limit, "pages": -(-total // limit)}


def add_statement(db: Session, policy_id: UUID, resource: str, action: str, effect: str, org_id: UUID) -> PolicyStatement:
    policy = db.query(Policy).filter(Policy.id == policy_id, Policy.org_id == org_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail={"error_code": "NOT_FOUND", "message": "Policy not found"})
    statement = PolicyStatement(id=uuid.uuid4(), policy_id=policy_id, resource=resource, action=action, effect=effect)
    db.add(statement)
    db.commit()
    db.refresh(statement)
    return statement


def remove_statement(db: Session, policy_id: UUID, statement_id: UUID, org_id: UUID):
    policy = db.query(Policy).filter(Policy.id == policy_id, Policy.org_id == org_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail={"error_code": "NOT_FOUND", "message": "Policy not found"})
    stmt = db.query(PolicyStatement).filter(
        PolicyStatement.id == statement_id,
        PolicyStatement.policy_id == policy_id,
    ).first()
    if not stmt:
        raise HTTPException(status_code=404, detail={"error_code": "NOT_FOUND", "message": "Statement not found"})
    db.delete(stmt)
    db.commit()
