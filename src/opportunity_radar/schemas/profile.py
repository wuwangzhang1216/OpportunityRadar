"""Profile schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AvailabilityBlock(BaseModel):
    """Availability time block."""

    dow: str  # Day of week: Mon, Tue, Wed, Thu, Fri, Sat, Sun
    start: str  # HH:mm format
    end: str  # HH:mm format


class ProfileBase(BaseModel):
    """Base profile schema."""

    profile_type: Optional[str] = None  # indie_hacker, student, startup
    stage: Optional[str] = None  # pre-seed, seed, series-a
    tech_stack: List[str] = Field(default_factory=list)
    industries: List[str] = Field(default_factory=list)
    team_size: int = 1
    availability: List[AvailabilityBlock] = Field(default_factory=list)
    wins: List[str] = Field(default_factory=list)
    intents: List[str] = Field(default_factory=list)  # funding, exposure, learning


class ProfileCreate(ProfileBase):
    """Schema for creating profile."""

    pass


class ProfileUpdate(BaseModel):
    """Schema for updating profile."""

    profile_type: Optional[str] = None
    stage: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    industries: Optional[List[str]] = None
    team_size: Optional[int] = None
    availability: Optional[List[AvailabilityBlock]] = None
    wins: Optional[List[str]] = None
    intents: Optional[List[str]] = None


class ProfileResponse(ProfileBase):
    """Schema for profile response."""

    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
