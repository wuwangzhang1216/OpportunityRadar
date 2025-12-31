"""Opportunity schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TimelineSchema(BaseModel):
    """Timeline schema."""

    registration_opens_at: Optional[datetime] = None
    registration_closes_at: Optional[datetime] = None
    event_starts_at: Optional[datetime] = None
    event_ends_at: Optional[datetime] = None
    submission_deadline: Optional[datetime] = None
    demo_at: Optional[datetime] = None
    results_at: Optional[datetime] = None
    timezone: str = "UTC"


class PrizeSchema(BaseModel):
    """Prize schema."""

    id: str
    prize_type: Optional[str] = None
    name: Optional[str] = None
    amount: Optional[float] = None
    currency: str = "USD"
    benefits: List[str] = Field(default_factory=list)


class BatchSchema(BaseModel):
    """Batch schema."""

    id: str
    opportunity_id: str
    year: Optional[int] = None
    season: Optional[str] = None
    remote_ok: bool = True
    regions: List[str] = Field(default_factory=list)
    team_min: int = 1
    team_max: Optional[int] = None
    student_only: bool = False
    startup_stages: List[str] = Field(default_factory=list)
    sponsors: List[str] = Field(default_factory=list)
    status: str = "upcoming"
    timeline: Optional[TimelineSchema] = None
    prizes: List[PrizeSchema] = Field(default_factory=list)


class HostSchema(BaseModel):
    """Host schema."""

    id: str
    name: str
    type: str
    country: Optional[str] = None
    website: Optional[str] = None
    reputation_score: float = 0.0


class OpportunityBase(BaseModel):
    """Base opportunity schema."""

    category: str
    title: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    industry: List[str] = Field(default_factory=list)
    tech_stack: List[str] = Field(default_factory=list)
    locale: List[str] = Field(default_factory=list)
    url: Optional[str] = None
    image_url: Optional[str] = None


class OpportunityCreate(OpportunityBase):
    """Schema for creating opportunity."""

    external_id: str
    source: str
    host_id: Optional[str] = None


class OpportunityResponse(OpportunityBase):
    """Schema for opportunity response."""

    id: str
    source: str
    credibility_score: float = 0.0
    created_at: datetime
    updated_at: datetime
    host: Optional[HostSchema] = None
    current_batch: Optional[BatchSchema] = None

    class Config:
        from_attributes = True


class OpportunityListResponse(BaseModel):
    """Schema for opportunity list response."""

    items: List[OpportunityResponse]
    total: int
    limit: int
    offset: int
