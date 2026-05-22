from pydantic import BaseModel
from uuid import UUID
from typing import List


class StatementCreate(BaseModel):
    resource: str
    action: str
    effect: str = "allow"


class StatementResponse(BaseModel):
    id: UUID
    resource: str
    action: str
    effect: str

    model_config = {"from_attributes": True}


class PolicyCreate(BaseModel):
    name: str


class PolicyResponse(BaseModel):
    id: UUID
    name: str
    org_id: UUID
    statements: List[StatementResponse] = []

    model_config = {"from_attributes": True}
