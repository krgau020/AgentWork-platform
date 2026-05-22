"""
Policy Schemas (app/schemas/policy.py)

Pydantic models for the policy and statement management API.
Policies are named permission sets. Statements are the individual rules inside a policy.

Classes:

    PolicyCreate — request body for POST /api/v1/policies
        Client sends only the name (e.g. "document-read").
        The server assigns id and org_id. No statements are created here —
        statements are added separately via POST /api/v1/policies/{id}/statements.

    PolicyResponse — returned by POST /api/v1/policies and GET /api/v1/policies
        Full policy record: id, name, org_id, and its list of statements.
        statements defaults to empty list — a new policy has no rules yet.
        model_config from_attributes=True lets Pydantic read from SQLAlchemy objects.

    StatementCreate — request body for POST /api/v1/policies/{id}/statements
        Defines one permission rule:
            resource — what is being accessed (e.g. "documents", "users", "*")
            action   — what operation (e.g. "read", "write", "delete", "*")
            effect   — "allow" or "deny" (defaults to "allow")
        The policy_id comes from the URL path, not the body.

    StatementResponse — returned after adding a statement
        The full statement record including the server-assigned id.

Relationship:
    PolicyCreate  →  creates a Policy (empty)
    StatementCreate → adds rules to that policy one at a time
    PolicyResponse  → shows the policy with all its statements included

Deployment note:
    Policies are org-scoped. A policy created in org A cannot be assigned to a
    group in org B. The service layer enforces this via org_id filtering on
    every query against the policies table.
"""

from pydantic import BaseModel, Field
from uuid import UUID
from typing import List


class StatementCreate(BaseModel):
    resource: str
    action: str
    effect: str = "allow"


class StatementResponse(BaseModel):
    statement_id: UUID = Field(validation_alias="id")
    resource: str
    action: str
    effect: str

    model_config = {"from_attributes": True}


class PolicyCreate(BaseModel):
    name: str


class PolicyResponse(BaseModel):
    policy_id: UUID = Field(validation_alias="id")
    name: str
    org_id: UUID
    statements: List[StatementResponse] = []

    model_config = {"from_attributes": True}
