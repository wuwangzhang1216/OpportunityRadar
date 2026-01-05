"""Schemas for shared lists and community features."""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class SharedListCreate(BaseModel):
    """Schema for creating a shared list."""

    title: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    visibility: Literal["private", "unlisted", "public"] = "private"
    tags: List[str] = Field(default_factory=list)
    opportunity_ids: List[str] = Field(default_factory=list)
    cover_image_url: Optional[str] = None


class SharedListUpdate(BaseModel):
    """Schema for updating a shared list."""

    title: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    visibility: Optional[Literal["private", "unlisted", "public"]] = None
    tags: Optional[List[str]] = None
    cover_image_url: Optional[str] = None


class CommentCreate(BaseModel):
    """Schema for creating a comment."""

    content: str = Field(..., min_length=1, max_length=500)


class CommentResponse(BaseModel):
    """Schema for comment in responses."""

    user_id: str
    user_name: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class OpportunityBrief(BaseModel):
    """Brief opportunity info for list responses."""

    id: str
    title: str
    opportunity_type: str
    website_url: Optional[str] = None
    application_deadline: Optional[datetime] = None
    total_prize_value: Optional[float] = None


class SharedListResponse(BaseModel):
    """Schema for shared list response."""

    id: str
    owner_id: str
    owner_name: str
    title: str
    slug: str
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    visibility: str
    opportunity_count: int
    tags: List[str] = []
    view_count: int = 0
    like_count: int = 0
    is_liked: bool = False
    comment_count: int = 0
    is_featured: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SharedListDetailResponse(SharedListResponse):
    """Schema for detailed shared list response with opportunities."""

    opportunities: List[OpportunityBrief] = []
    comments: List[CommentResponse] = []


class SharedListListResponse(BaseModel):
    """Schema for paginated list of shared lists."""

    items: List[SharedListResponse]
    total: int
    skip: int
    limit: int


class ShareLinkResponse(BaseModel):
    """Schema for share link response."""

    url: str
    embed_code: Optional[str] = None
