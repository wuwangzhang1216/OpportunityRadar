"""Match schemas."""

from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    """Score breakdown for a match."""

    semantic_similarity: float = 0.0
    hard_fit: float = 0.0
    preference_fit: float = 0.0
    time_feasibility: float = 0.0
    team_fit: float = 0.0
    past_win_bonus: float = 0.0


class MismatchReason(BaseModel):
    """Reason for mismatch."""

    reason: str
    severity: str  # blocking, warning, info
    fix_suggestion: Optional[str] = None


class MatchResponse(BaseModel):
    """Schema for match response."""

    id: str
    profile_id: str
    batch_id: str
    score: float
    score_breakdown: ScoreBreakdown
    mismatch_reasons: List[MismatchReason] = Field(default_factory=list)
    status: str = "pending"  # pending, interested, applied, dismissed
    created_at: datetime
    updated_at: datetime

    # Include opportunity summary
    opportunity_title: Optional[str] = None
    opportunity_category: Optional[str] = None
    deadline: Optional[datetime] = None

    class Config:
        from_attributes = True


class MatchListResponse(BaseModel):
    """Schema for match list response."""

    items: List[MatchResponse]
    total: int
