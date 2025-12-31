"""Pipeline model for MongoDB."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


class Pipeline(Document):
    """User's opportunity tracking pipeline."""

    user_id: Indexed(PydanticObjectId)
    opportunity_id: Indexed(PydanticObjectId)
    match_id: Optional[PydanticObjectId] = None
    status: str = "interested"  # interested, preparing, submitted, won, lost
    notes: Optional[str] = None
    team_members: List[Dict[str, Any]] = Field(default_factory=list)
    project_idea: Optional[str] = None
    submission_url: Optional[str] = None
    reminder_enabled: bool = True
    last_reminder_sent: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "pipelines"
        indexes = [
            [("user_id", 1), ("opportunity_id", 1)],
        ]
