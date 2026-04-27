"""
Pydantic schemas for user endpoints.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool

    class Config:
        from_attributes = True


class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
