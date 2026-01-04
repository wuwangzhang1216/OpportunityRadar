"""Material generation schemas."""

from datetime import datetime
from typing import List, Optional, Dict, Any, Literal

from pydantic import BaseModel, Field, field_validator


# Valid material targets
VALID_TARGETS = {"readme", "pitch_1min", "pitch_3min", "pitch_5min", "demo_script", "qa_pred"}
MAX_TARGETS = 6  # Maximum number of targets per request


class ProjectInfo(BaseModel):
    """Project information for material generation."""

    name: str = Field(..., min_length=1, max_length=200)
    problem: str = Field(..., min_length=10, max_length=5000)
    solution: str = Field(..., min_length=10, max_length=5000)
    tech_stack: List[str] = Field(default_factory=list, max_length=20)
    demo_url: Optional[str] = Field(default=None, max_length=500)

    @field_validator("tech_stack")
    @classmethod
    def filter_empty_tech_stack(cls, v: List[str]) -> List[str]:
        """Remove empty strings from tech stack."""
        return [item.strip() for item in v if item and item.strip()]


class GenerationConstraints(BaseModel):
    """Constraints for material generation."""

    highlight_demo: bool = False
    time_limit_min: Optional[int] = Field(default=None, ge=1, le=10)
    include_user_evidence: bool = False


class MaterialGenerateRequest(BaseModel):
    """Schema for material generation request."""

    opportunity_id: Optional[str] = Field(
        default=None,
        description="Optional opportunity ID for context-aware generation",
        max_length=24,
    )
    targets: List[str] = Field(
        default=["readme", "pitch_3min"],
        description="List of targets: readme, pitch_1min, pitch_3min, pitch_5min, demo_script, qa_pred",
        min_length=1,
        max_length=MAX_TARGETS,
    )
    language: str = Field(default="en", max_length=10)
    project_info: ProjectInfo
    constraints: GenerationConstraints = Field(default_factory=GenerationConstraints)

    @field_validator("targets")
    @classmethod
    def validate_targets(cls, v: List[str]) -> List[str]:
        """Validate that all targets are valid and unique."""
        # Remove duplicates while preserving order
        seen = set()
        unique_targets = []
        for target in v:
            if target not in seen:
                seen.add(target)
                unique_targets.append(target)

        # Validate each target
        invalid = [t for t in unique_targets if t not in VALID_TARGETS]
        if invalid:
            raise ValueError(
                f"Invalid targets: {invalid}. Valid targets are: {sorted(VALID_TARGETS)}"
            )

        return unique_targets

    @field_validator("opportunity_id")
    @classmethod
    def validate_opportunity_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate opportunity ID format if provided."""
        if v is not None and len(v) != 24:
            raise ValueError("Invalid opportunity ID format")
        return v


class GenerationError(BaseModel):
    """Schema for a single generation error."""

    target: str
    error: str


class MaterialResponse(BaseModel):
    """Schema for material generation response."""

    readme_md: Optional[str] = None
    pitch_md: Optional[str] = None
    demo_script_md: Optional[str] = None
    qa_pred_md: Optional[str] = None
    budget_json: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    errors: List[GenerationError] = Field(default_factory=list)


class SavedMaterial(BaseModel):
    """Schema for saved material."""

    id: str
    user_id: str
    opportunity_id: Optional[str] = None
    material_type: str
    content: str
    version: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True
