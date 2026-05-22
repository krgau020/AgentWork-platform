from pydantic import BaseModel
from uuid import UUID
from typing import List


class UserResponse(BaseModel):
    id: UUID
    email: str
    org_id: UUID
    is_active: bool

    model_config = {"from_attributes": True}


class GroupAssign(BaseModel):
    group_id: UUID


class UserPoliciesResponse(BaseModel):
    user_id: UUID
    policies: List[dict]
