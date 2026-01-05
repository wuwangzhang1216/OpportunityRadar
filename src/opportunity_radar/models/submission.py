"""User-submitted opportunity model for MongoDB."""

from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional, Any

from beanie import Document, Indexed, PydanticObjectId
from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    """Return current UTC time with timezone info."""
    return datetime.now(timezone.utc)


SubmissionStatus = Literal["pending", "approved", "rejected", "needs_info"]


class ReviewNote(BaseModel):
    """Admin review note."""

    reviewer_id: PydanticObjectId
    note: str
    status_change: Optional[str] = None
    created_at: datetime = Field(default_factory=_utc_now)


class OpportunitySubmission(Document):
    """User-submitted opportunity for review."""

    # Submitter info
    submitted_by: Indexed(PydanticObjectId)
    submitter_email: str

    # Opportunity details
    title: str
    description: str
    opportunity_type: str = "hackathon"  # hackathon, grant, competition, bounty, accelerator
    format: Optional[str] = None  # online, in-person, hybrid
    website_url: str
    logo_url: Optional[str] = None

    # Organization
    host_name: str
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
    team_size_min: Optional[int] = None
    team_size_max: Optional[int] = None
    eligibility_notes: Optional[str] = None

    # Social/contact
    contact_email: Optional[str] = None
    social_links: Dict[str, str] = Field(default_factory=dict)

    # Review status
    status: SubmissionStatus = "pending"
    review_notes: List[ReviewNote] = Field(default_factory=list)
    reviewed_by: Optional[PydanticObjectId] = None
    reviewed_at: Optional[datetime] = None

    # If approved, link to created opportunity
    opportunity_id: Optional[PydanticObjectId] = None

    # Timestamps
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)

    class Settings:
        name = "opportunity_submissions"
        indexes = [
            "submitted_by",
            "status",
            "created_at",
        ]

    def add_review_note(
        self,
        reviewer_id: PydanticObjectId,
        note: str,
        status_change: Optional[str] = None,
    ) -> None:
        """Add a review note."""
        self.review_notes.append(
            ReviewNote(
                reviewer_id=reviewer_id,
                note=note,
                status_change=status_change,
            )
        )
        self.updated_at = _utc_now()
