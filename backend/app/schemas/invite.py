"""
Pydantic schemas for invite endpoints.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class CreateInviteRequest(BaseModel):
    email: EmailStr
    role: str = Field(default="member", pattern=r"^(admin|member)$")


class AcceptInviteRequest(BaseModel):
    token: str


class InviteResponse(BaseModel):
    id: str
    email: str
    role: str
    status: str
    invited_by: str
    inviter_name: Optional[str] = None
    expires_at: datetime
    created_at: datetime
    org_id: str

    class Config:
        from_attributes = True
