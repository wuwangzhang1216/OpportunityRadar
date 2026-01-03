"""ScraperRun model for tracking scraper execution history."""

from datetime import datetime, timezone
from typing import Literal

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


def _utc_now() -> datetime:
    """Return current UTC time with timezone info."""
    return datetime.now(timezone.utc)


class ScraperRun(Document):
    """Record of a scraper execution."""

    scraper_name: Indexed(str)
    status: Literal["pending", "running", "success", "partial", "failed"] = "pending"
    started_at: Indexed(datetime) = Field(default_factory=_utc_now)
    completed_at: datetime | None = None
    opportunities_found: int = 0
    opportunities_created: int = 0
    opportunities_updated: int = 0
    errors: list[str] = Field(default_factory=list)
    triggered_by: PydanticObjectId | None = None  # Admin user ID if manual trigger

    class Settings:
        name = "scraper_runs"
        indexes = [
            "status",  # For filtering by status
        ]

    def mark_running(self) -> None:
        """Mark the run as started."""
        self.status = "running"
        self.started_at = _utc_now()

    def mark_success(self) -> None:
        """Mark the run as completed successfully."""
        self.status = "success"
        self.completed_at = _utc_now()

    def mark_partial(self) -> None:
        """Mark the run as partially successful (some errors)."""
        self.status = "partial"
        self.completed_at = _utc_now()

    def mark_failed(self, error: str | None = None) -> None:
        """Mark the run as failed."""
        self.status = "failed"
        self.completed_at = _utc_now()
        if error:
            self.errors.append(error)

    def add_error(self, error: str) -> None:
        """Add an error to the run."""
        self.errors.append(error)

    @property
    def duration_seconds(self) -> float | None:
        """Calculate duration in seconds."""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
