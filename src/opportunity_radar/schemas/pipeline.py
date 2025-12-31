"""Pipeline schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PipelineBase(BaseModel):
    """Base pipeline schema."""

    batch_id: str
    stage: str = "discovered"  # discovered, preparing, submitted, pending, won, lost
    eta_hours: Optional[int] = None
    notes: Optional[str] = None


class PipelineCreate(PipelineBase):
    """Schema for creating pipeline item."""

    pass


class PipelineUpdate(BaseModel):
    """Schema for updating pipeline item."""

    stage: Optional[str] = None
    eta_hours: Optional[int] = None
    notes: Optional[str] = None


class PipelineResponse(PipelineBase):
    """Schema for pipeline response."""

    id: str
    user_id: str
    deadline_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Include opportunity summary
    opportunity_title: Optional[str] = None
    opportunity_category: Optional[str] = None

    class Config:
        from_attributes = True
