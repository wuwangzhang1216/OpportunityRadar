"""Onboarding schemas for URL extraction and profile creation."""

from enum import Enum
from typing import Any, List, Optional, Union

from pydantic import BaseModel, Field, HttpUrl, field_validator


class URLType(str, Enum):
    """Type of URL being processed."""

    WEBSITE = "website"
    GITHUB_REPO = "github_repo"


class ExtractedField(BaseModel):
    """A field extracted by AI with confidence score."""

    value: Union[str, List[str], int, None]
    confidence: float = Field(ge=0, le=1, description="Confidence score 0-1")
    source: str = Field(description="Where this was extracted from")


class ExtractedProfile(BaseModel):
    """Profile information extracted from URL by AI."""

    url_type: URLType
    source_url: str

    # Extracted fields with confidence
    company_name: Optional[ExtractedField] = None
    product_description: Optional[ExtractedField] = None
    tech_stack: Optional[ExtractedField] = None
    industries: Optional[ExtractedField] = None
    team_size: Optional[ExtractedField] = None
    profile_type: Optional[ExtractedField] = None
    location: Optional[ExtractedField] = None
    goals: Optional[ExtractedField] = None

    # Raw content for debugging
    raw_content_preview: Optional[str] = Field(
        None, description="Preview of scraped content (first 500 chars)"
    )


class URLExtractRequest(BaseModel):
    """Request to extract profile from URL."""

    url: str = Field(description="Website or GitHub repo URL")


class URLExtractResponse(BaseModel):
    """Response from URL extraction."""

    success: bool
    extracted_profile: Optional[ExtractedProfile] = None
    error_message: Optional[str] = None


class OnboardingConfirmRequest(BaseModel):
    """Request to confirm and create profile from extracted data."""

    # User-confirmed values (after editing extracted data)
    display_name: str = Field(..., min_length=1, description="Display name is required")
    bio: Optional[str] = None
    tech_stack: List[str] = Field(..., min_length=1, description="At least one tech stack item required")
    industries: List[str] = Field(default_factory=list)
    goals: List[str] = Field(..., min_length=1, description="At least one goal required")
    interests: List[str] = Field(default_factory=list)
    experience_level: Optional[str] = None
    team_size: int = Field(default=1, ge=1, le=100)
    profile_type: str = Field(default="developer")
    location_country: Optional[str] = None
    location_region: Optional[str] = None

    # Source URL for reference
    source_url: Optional[str] = None

    @field_validator('display_name')
    @classmethod
    def display_name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Display name is required')
        return v.strip()

    @field_validator('tech_stack')
    @classmethod
    def tech_stack_not_empty(cls, v: List[str]) -> List[str]:
        if not v or len(v) == 0:
            raise ValueError('At least one tech stack item is required')
        return v

    @field_validator('goals')
    @classmethod
    def goals_not_empty(cls, v: List[str]) -> List[str]:
        if not v or len(v) == 0:
            raise ValueError('At least one goal is required')
        return v


class OnboardingConfirmResponse(BaseModel):
    """Response from profile confirmation."""

    success: bool
    profile_id: Optional[str] = None
    onboarding_completed: bool = False
    error_message: Optional[str] = None


class OnboardingStatusResponse(BaseModel):
    """Response for onboarding status check."""

    has_profile: bool
    onboarding_completed: bool
    profile_id: Optional[str] = None


# Predefined options for UI dropdowns
class ProfileTypeOption(str, Enum):
    """Profile type options."""

    DEVELOPER = "developer"
    STARTUP = "startup"
    STUDENT = "student"
    RESEARCHER = "researcher"
    FREELANCER = "freelancer"


class ExperienceLevelOption(str, Enum):
    """Experience level options."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


# Common tech stacks for suggestions
COMMON_TECH_STACKS = [
    "Python",
    "JavaScript",
    "TypeScript",
    "React",
    "Next.js",
    "Node.js",
    "Go",
    "Rust",
    "Java",
    "C++",
    "C#",
    "Swift",
    "Kotlin",
    "Ruby",
    "PHP",
    "Vue.js",
    "Angular",
    "Django",
    "FastAPI",
    "Flask",
    "Spring Boot",
    "PostgreSQL",
    "MongoDB",
    "Redis",
    "AWS",
    "GCP",
    "Azure",
    "Docker",
    "Kubernetes",
    "TensorFlow",
    "PyTorch",
    "Machine Learning",
    "Blockchain",
    "Solidity",
    "Web3",
]

# Common goals for suggestions
COMMON_GOALS = [
    "Win hackathons",
    "Build portfolio",
    "Learn new technologies",
    "Network with developers",
    "Find co-founders",
    "Get funding",
    "Launch a startup",
    "Contribute to open source",
    "Find bug bounties",
    "Apply for grants",
]

# Common industries for suggestions
COMMON_INDUSTRIES = [
    "FinTech",
    "HealthTech",
    "EdTech",
    "E-commerce",
    "SaaS",
    "AI/ML",
    "Blockchain/Crypto",
    "Gaming",
    "Social Media",
    "Developer Tools",
    "Cybersecurity",
    "IoT",
    "CleanTech",
    "BioTech",
    "Real Estate",
    "Travel",
    "Food & Beverage",
    "Entertainment",
    "Government",
    "Non-profit",
]
