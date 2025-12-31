"""Match model for MongoDB."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


class Match(Document):
    """Match between a user and an opportunity."""

    user_id: Indexed(PydanticObjectId)
    opportunity_id: Indexed(PydanticObjectId)
    overall_score: float = 0.0
    semantic_score: Optional[float] = None
    rule_score: Optional[float] = None
    time_score: Optional[float] = None
    team_score: Optional[float] = None
    score_breakdown: Optional[Dict[str, Any]] = None
    eligibility_status: Optional[str] = None  # eligible, partial, ineligible
    eligibility_issues: List[str] = Field(default_factory=list)
    fix_suggestions: List[str] = Field(default_factory=list)
    is_bookmarked: bool = False
    is_dismissed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "matches"
        indexes = [
            [("user_id", 1), ("opportunity_id", 1)],
        ]
