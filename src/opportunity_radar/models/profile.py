"""Profile model for MongoDB."""

from datetime import datetime
from typing import List, Optional

from beanie import Document, PydanticObjectId
from pydantic import Field


class Profile(Document):
    """User profile with skills, preferences, and embedding."""

    user_id: PydanticObjectId
    display_name: Optional[str] = None
    bio: Optional[str] = None
    tech_stack: List[str] = Field(default_factory=list)
    experience_level: Optional[str] = None
    availability_hours_per_week: Optional[int] = None
    timezone: Optional[str] = None
    preferred_team_size_min: int = 1
    preferred_team_size_max: int = 5
    goals: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    location_country: Optional[str] = None
    location_region: Optional[str] = None
    student_status: Optional[str] = None
    university: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "profiles"
