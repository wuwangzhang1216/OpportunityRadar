"""ScraperRun model for tracking scraper execution history."""

from datetime import datetime
from typing import List, Literal, Optional

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


class ScraperRun(Document):
    """Record of a scraper execution."""

    scraper_name: Indexed(str)
    status: Literal["pending", "running", "success", "partial", "failed"] = "pending"
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    opportunities_found: int = 0
    opportunities_created: int = 0
    opportunities_updated: int = 0
    errors: List[str] = Field(default_factory=list)
    triggered_by: Optional[PydanticObjectId] = None  # Admin user ID if manual trigger

    class Settings:
        name = "scraper_runs"

    def mark_running(self):
        """Mark the run as started."""
        self.status = "running"
        self.started_at = datetime.utcnow()

    def mark_success(self):
        """Mark the run as completed successfully."""
        self.status = "success"
        self.completed_at = datetime.utcnow()

    def mark_partial(self):
        """Mark the run as partially successful (some errors)."""
        self.status = "partial"
        self.completed_at = datetime.utcnow()

    def mark_failed(self, error: str = None):
        """Mark the run as failed."""
        self.status = "failed"
        self.completed_at = datetime.utcnow()
        if error:
            self.errors.append(error)

    def add_error(self, error: str):
        """Add an error to the run."""
        self.errors.append(error)

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate duration in seconds."""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
