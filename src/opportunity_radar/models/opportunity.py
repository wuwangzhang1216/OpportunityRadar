"""Opportunity and Host models for MongoDB."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


class Host(Document):
    """Host/organization that provides opportunities."""

    name: Indexed(str, unique=True)
    slug: Indexed(str, unique=True)
    website_url: Optional[str] = None
    logo_url: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "hosts"


class Opportunity(Document):
    """Opportunity (hackathon, grant, competition)."""

    host_id: Optional[PydanticObjectId] = None
    external_id: Indexed(str)
    title: str
    slug: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    opportunity_type: str = "hackathon"  # hackathon, grant, competition
    format: Optional[str] = None  # online, in-person, hybrid
    location_type: Optional[str] = None
    location_city: Optional[str] = None
    location_country: Optional[str] = None
    website_url: Optional[str] = None
    registration_url: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    themes: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    sponsors: List[Dict[str, Any]] = Field(default_factory=list)
    judges: List[Dict[str, Any]] = Field(default_factory=list)
    prizes: List[Dict[str, Any]] = Field(default_factory=list)
    requirements: List[Dict[str, Any]] = Field(default_factory=list)
    timelines: List[Dict[str, Any]] = Field(default_factory=list)
    total_prize_value: Optional[float] = None
    currency: str = "USD"
    participant_count: Optional[int] = None
    team_size_min: Optional[int] = None
    team_size_max: Optional[int] = None
    is_featured: bool = False
    is_active: bool = True
    source_url: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "opportunities"
        indexes = [
            [("host_id", 1), ("external_id", 1)],
        ]
