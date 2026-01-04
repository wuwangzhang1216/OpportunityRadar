"""Material generation schemas."""

from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class ProjectInfo(BaseModel):
    """Project information for material generation."""

    name: str
    problem: str
    solution: str
    tech_stack: List[str] = Field(default_factory=list)
    demo_url: Optional[str] = None


class GenerationConstraints(BaseModel):
    """Constraints for material generation."""

    highlight_demo: bool = False
    time_limit_min: Optional[int] = None  # For pitch
    include_user_evidence: bool = False


class MaterialGenerateRequest(BaseModel):
    """Schema for material generation request."""

    opportunity_id: Optional[str] = Field(
        default=None,
        description="Optional opportunity ID for context-aware generation",
    )
    targets: List[str] = Field(
        default=["readme", "pitch_3min"],
        description="List of targets: readme, pitch_1min, pitch_3min, pitch_5min, demo_script, qa_pred",
    )
    language: str = "en"
    project_info: ProjectInfo
    constraints: GenerationConstraints = Field(default_factory=GenerationConstraints)


class MaterialResponse(BaseModel):
    """Schema for material generation response."""

    readme_md: Optional[str] = None
    pitch_md: Optional[str] = None
    demo_script_md: Optional[str] = None
    qa_pred_md: Optional[str] = None
    budget_json: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SavedMaterial(BaseModel):
    """Schema for saved material."""

    id: str
    user_id: str
    batch_id: Optional[str] = None
    material_type: str
    content: str
    version: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True
