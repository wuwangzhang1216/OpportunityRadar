"""Material model for MongoDB."""

from datetime import datetime
from typing import Dict, Optional, Any

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


class Material(Document):
    """Generated materials (README, pitch, etc.)."""

    user_id: Indexed(PydanticObjectId)
    opportunity_id: Optional[PydanticObjectId] = None
    pipeline_id: Optional[PydanticObjectId] = None
    material_type: Indexed(str)  # readme, pitch_3min, demo_script, qa_pred
    title: Optional[str] = None
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    prompt_used: Optional[str] = None
    model_used: Optional[str] = None
    is_favorite: bool = False
    version: int = 1
    parent_id: Optional[PydanticObjectId] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "materials"
