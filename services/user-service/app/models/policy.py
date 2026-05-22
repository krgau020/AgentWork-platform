"""
Policy and PolicyStatement Models (app/models/policy.py)

Two models in one file because they are tightly coupled.

Policy:
  A named permission set belonging to one org.
  Example: "document-read", "full-access", "billing-manage"
  The name is just a human-readable label — it does not control anything.
  The actual rules live in PolicyStatement rows.

PolicyStatement:
  One permission rule inside a policy.
  Three fields define what is allowed or denied:
    resource — what thing is being accessed (e.g. "documents", "users", "*")
    action   — what operation (e.g. "read", "write", "delete", "*")
    effect   — "allow" or "deny"

  Example statement:
    { resource: "documents", action: "read", effect: "allow" }
    Meaning: "reading documents is allowed"

One policy can have many statements:
  policy "manager-access":
    { resource: "documents", action: "read",   effect: "allow" }
    { resource: "documents", action: "write",  effect: "allow" }
    { resource: "users",     action: "read",   effect: "allow" }

Why separate table for statements instead of a JSON column:
  Separate rows let you add/remove individual rules without rewriting the whole policy.
  Indexing and querying individual rules is also faster in a normalized structure.
"""

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class Policy(Base):
    __tablename__ = "policies"

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    org_id = Column(UUID(as_uuid=True), nullable=False)


class PolicyStatement(Base):
    __tablename__ = "policy_statements"

    id = Column(UUID(as_uuid=True), primary_key=True)
    policy_id = Column(UUID(as_uuid=True), nullable=False)
    resource = Column(String, nullable=False)
    action = Column(String, nullable=False)
    effect = Column(String, nullable=False, default="allow")
