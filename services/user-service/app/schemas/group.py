from pydantic import BaseModel
from uuid import UUID


class GroupCreate(BaseModel):
    name: str


class GroupResponse(BaseModel):
    id: UUID
    name: str
    org_id: UUID

    model_config = {"from_attributes": True}


class PolicyAssign(BaseModel):
    policy_id: UUID
