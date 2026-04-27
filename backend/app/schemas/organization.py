"""
Pydantic schemas for organization endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CreateOrgRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=255, pattern=r"^[a-z0-9\-]+$")


class UpdateOrgRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)


class OrgResponse(BaseModel):
    id: str
    name: str
    slug: str
    created_by: str
    created_at: datetime
    member_count: Optional[int] = None

    class Config:
        from_attributes = True


class MemberResponse(BaseModel):
    id: str
    user_id: str
    email: str
    full_name: str
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class UpdateMemberRoleRequest(BaseModel):
    role: str = Field(..., pattern=r"^(admin|member)$")
