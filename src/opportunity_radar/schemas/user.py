"""User schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating user."""

    full_name: Optional[str] = None


class UserResponse(BaseModel):
    """Schema for user response."""

    id: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    has_profile: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for token payload."""

    sub: str
    exp: datetime
    type: str
