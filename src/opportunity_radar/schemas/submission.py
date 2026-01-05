"""Schemas for user-submitted opportunities."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class SubmissionCreate(BaseModel):
    """Schema for creating a new opportunity submission."""

    # Required fields
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=50, max_length=5000)
    website_url: str = Field(..., description="Official opportunity URL")
    host_name: str = Field(..., min_length=2, max_length=100)

    # Optional opportunity details
    opportunity_type: str = Field(default="hackathon")
    format: Optional[str] = Field(None, description="online, in-person, or hybrid")
    logo_url: Optional[str] = None
    host_website: Optional[str] = None

    # Location
    location_type: Optional[str] = None
    location_city: Optional[str] = None
    location_country: Optional[str] = None

    # Dates
    application_deadline: Optional[datetime] = None
    event_start_date: Optional[datetime] = None
    event_end_date: Optional[datetime] = None

    # Details
    themes: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    total_prize_value: Optional[float] = None
    currency: str = "USD"
    team_size_min: Optional[int] = Field(None, ge=1, le=20)
    team_size_max: Optional[int] = Field(None, ge=1, le=100)
    eligibility_notes: Optional[str] = Field(None, max_length=1000)

    # Contact
    contact_email: Optional[str] = None
    social_links: Dict[str, str] = Field(default_factory=dict)


class SubmissionUpdate(BaseModel):
    """Schema for updating a submission (by submitter)."""

    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, min_length=50, max_length=5000)
    website_url: Optional[str] = None
    host_name: Optional[str] = Field(None, min_length=2, max_length=100)
    opportunity_type: Optional[str] = None
    format: Optional[str] = None
    logo_url: Optional[str] = None
    host_website: Optional[str] = None
    location_type: Optional[str] = None
    location_city: Optional[str] = None
    location_country: Optional[str] = None
    application_deadline: Optional[datetime] = None
    event_start_date: Optional[datetime] = None
    event_end_date: Optional[datetime] = None
    themes: Optional[List[str]] = None
    technologies: Optional[List[str]] = None
    total_prize_value: Optional[float] = None
    currency: Optional[str] = None
    team_size_min: Optional[int] = Field(None, ge=1, le=20)
    team_size_max: Optional[int] = Field(None, ge=1, le=100)
    eligibility_notes: Optional[str] = Field(None, max_length=1000)
    contact_email: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None


class ReviewNoteResponse(BaseModel):
    """Schema for review note in responses."""

    reviewer_id: str
    note: str
    status_change: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SubmissionResponse(BaseModel):
    """Schema for submission response."""

    id: str
    submitted_by: str
    title: str
    description: str
    opportunity_type: str
    format: Optional[str] = None
    website_url: str
    logo_url: Optional[str] = None
    host_name: str
    host_website: Optional[str] = None
    location_type: Optional[str] = None
    location_city: Optional[str] = None
    location_country: Optional[str] = None
    application_deadline: Optional[datetime] = None
    event_start_date: Optional[datetime] = None
    event_end_date: Optional[datetime] = None
    themes: List[str] = []
    technologies: List[str] = []
    total_prize_value: Optional[float] = None
    currency: str = "USD"
    team_size_min: Optional[int] = None
    team_size_max: Optional[int] = None
    eligibility_notes: Optional[str] = None
    contact_email: Optional[str] = None
    social_links: Dict[str, str] = {}
    status: str
    review_notes: List[ReviewNoteResponse] = []
    opportunity_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubmissionListResponse(BaseModel):
    """Schema for paginated submission list."""

    items: List[SubmissionResponse]
    total: int
    skip: int
    limit: int


class AdminReviewRequest(BaseModel):
    """Schema for admin review action."""

    status: str = Field(..., description="New status: approved, rejected, or needs_info")
    note: str = Field(..., min_length=5, max_length=1000, description="Review note")


class SubmissionStats(BaseModel):
    """Statistics about submissions."""

    total: int
    pending: int
    approved: int
    rejected: int
    needs_info: int
