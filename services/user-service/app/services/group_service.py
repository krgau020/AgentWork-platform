"""
Group Service

All group operations are scoped to org_id — a group from one org
is invisible to another org even if names match.
"""

import uuid
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.group import Group
from app.models.group_policy import GroupPolicy
from app.models.user_group import UserGroup


def create_group(db: Session, name: str, org_id: UUID) -> Group:
    existing = db.query(Group).filter(Group.name == name, Group.org_id == org_id).first()
    if existing:
        raise HTTPException(status_code=409, detail={
            "error_code": "CONFLICT",
            "message": f"Group '{name}' already exists in this org",
        })
    group = Group(id=uuid.uuid4(), name=name, org_id=org_id)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def list_groups(db: Session, org_id: UUID, page: int, limit: int) -> dict:
    query = db.query(Group).filter(Group.org_id == org_id)
    total = query.count()
    groups = query.offset((page - 1) * limit).limit(limit).all()
    return {"data": groups, "total": total, "page": page, "limit": limit, "pages": -(-total // limit)}


def assign_policy(db: Session, group_id: UUID, policy_id: UUID, org_id: UUID):
    group = db.query(Group).filter(Group.id == group_id, Group.org_id == org_id).first()
    if not group:
        raise HTTPException(status_code=404, detail={"error_code": "NOT_FOUND", "message": "Group not found"})
    existing = db.query(GroupPolicy).filter(
        GroupPolicy.group_id == group_id,
        GroupPolicy.policy_id == policy_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail={"error_code": "CONFLICT", "message": "Policy already assigned"})
    db.add(GroupPolicy(group_id=group_id, policy_id=policy_id))
    db.commit()


def remove_policy(db: Session, group_id: UUID, policy_id: UUID, org_id: UUID):
    group = db.query(Group).filter(Group.id == group_id, Group.org_id == org_id).first()
    if not group:
        raise HTTPException(status_code=404, detail={"error_code": "NOT_FOUND", "message": "Group not found"})
    link = db.query(GroupPolicy).filter(
        GroupPolicy.group_id == group_id,
        GroupPolicy.policy_id == policy_id,
    ).first()
    if not link:
        raise HTTPException(status_code=404, detail={"error_code": "NOT_FOUND", "message": "Policy not assigned to group"})
    db.delete(link)
    db.commit()


def add_user_to_group(db: Session, user_id: UUID, group_id: UUID, org_id: UUID):
    group = db.query(Group).filter(Group.id == group_id, Group.org_id == org_id).first()
    if not group:
        raise HTTPException(status_code=404, detail={"error_code": "NOT_FOUND", "message": "Group not found"})
    existing = db.query(UserGroup).filter(
        UserGroup.user_id == user_id, UserGroup.group_id == group_id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail={"error_code": "CONFLICT", "message": "User already in group"})
    db.add(UserGroup(user_id=user_id, group_id=group_id))
    db.commit()


def remove_user_from_group(db: Session, user_id: UUID, group_id: UUID, org_id: UUID):
    group = db.query(Group).filter(Group.id == group_id, Group.org_id == org_id).first()
    if not group:
        raise HTTPException(status_code=404, detail={"error_code": "NOT_FOUND", "message": "Group not found"})
    link = db.query(UserGroup).filter(
        UserGroup.user_id == user_id, UserGroup.group_id == group_id
    ).first()
    if not link:
        raise HTTPException(status_code=404, detail={"error_code": "NOT_FOUND", "message": "User not in group"})
    db.delete(link)
    db.commit()
