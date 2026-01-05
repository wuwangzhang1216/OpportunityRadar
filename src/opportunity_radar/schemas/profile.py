"""Profile schemas."""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# Type definitions
CompanyStage = Literal["idea", "prototype", "mvp", "launched", "revenue", "funded"]
FundingStage = Literal["bootstrapped", "pre_seed", "seed", "series_a", "series_b_plus"]
ProductStage = Literal["concept", "development", "beta", "live"]


class AvailabilityBlock(BaseModel):
    """Availability time block."""

    dow: str  # Day of week: Mon, Tue, Wed, Thu, Fri, Sat, Sun
    start: str  # HH:mm format
    end: str  # HH:mm format


class TeamMemberSchema(BaseModel):
    """Team member schema."""

    name: str
    role: str  # CEO, CTO, Engineer, Designer, etc.
    linkedin_url: Optional[str] = None
    skills: List[str] = Field(default_factory=list)


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

    # Team/Company Info
    team_name: Optional[str] = None
    company_stage: Optional[CompanyStage] = None

    # Funding Info
    funding_stage: Optional[FundingStage] = None
    seeking_funding: bool = False
    funding_amount_seeking: Optional[str] = None

    # Product Info
    product_name: Optional[str] = None
    product_description: Optional[str] = None
    product_url: Optional[str] = None
    product_stage: Optional[ProductStage] = None

    # Team Members
    team_members: List[TeamMemberSchema] = Field(default_factory=list)

    # Track Record
    previous_accelerators: List[str] = Field(default_factory=list)
    previous_hackathon_wins: int = 0
    notable_achievements: List[str] = Field(default_factory=list)


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

    # Team/Company Info
    team_name: Optional[str] = None
    company_stage: Optional[CompanyStage] = None

    # Funding Info
    funding_stage: Optional[FundingStage] = None
    seeking_funding: Optional[bool] = None
    funding_amount_seeking: Optional[str] = None

    # Product Info
    product_name: Optional[str] = None
    product_description: Optional[str] = None
    product_url: Optional[str] = None
    product_stage: Optional[ProductStage] = None

    # Team Members
    team_members: Optional[List[TeamMemberSchema]] = None

    # Track Record
    previous_accelerators: Optional[List[str]] = None
    previous_hackathon_wins: Optional[int] = None
    notable_achievements: Optional[List[str]] = None


class ProfileResponse(ProfileBase):
    """Schema for profile response."""

    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
