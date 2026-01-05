"""Profile model for MongoDB."""

from datetime import datetime
from typing import List, Literal, Optional

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field


# Company/Startup stage options
CompanyStage = Literal["idea", "prototype", "mvp", "launched", "revenue", "funded"]

# Funding stage options
FundingStage = Literal["bootstrapped", "pre_seed", "seed", "series_a", "series_b_plus"]

# Product stage options
ProductStage = Literal["concept", "development", "beta", "live"]


class TeamMember(BaseModel):
    """Team member information."""

    name: str
    role: str  # CEO, CTO, Engineer, Designer, etc.
    linkedin_url: Optional[str] = None
    skills: List[str] = Field(default_factory=list)


class Profile(Document):
    """User profile with skills, preferences, team info, and embedding."""

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

    # Team/Company Info
    team_name: Optional[str] = None  # Company or team name
    team_size: Optional[int] = None  # Number of team members
    company_stage: Optional[CompanyStage] = None  # idea, prototype, mvp, launched, revenue, funded

    # Funding Info
    funding_stage: Optional[FundingStage] = None  # bootstrapped, pre_seed, seed, series_a, series_b_plus
    seeking_funding: bool = False
    funding_amount_seeking: Optional[str] = None  # "$500K - $1M"

    # Product Info
    product_name: Optional[str] = None
    product_description: Optional[str] = None
    product_url: Optional[str] = None
    product_stage: Optional[ProductStage] = None  # concept, development, beta, live

    # Team Members
    team_members: List[TeamMember] = Field(default_factory=list)

    # Track Record / Previous Experience
    previous_accelerators: List[str] = Field(default_factory=list)  # ["YC", "Techstars"]
    previous_hackathon_wins: int = 0
    notable_achievements: List[str] = Field(default_factory=list)

    # Embedding for matching
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "profiles"
