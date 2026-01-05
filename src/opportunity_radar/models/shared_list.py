"""Shared opportunity list model for community features."""

from datetime import datetime, timezone
from typing import List, Literal, Optional

from beanie import Document, Indexed, PydanticObjectId
from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    """Return current UTC time with timezone info."""
    return datetime.now(timezone.utc)


ListVisibility = Literal["private", "unlisted", "public"]


class ListComment(BaseModel):
    """Comment on a shared list."""

    user_id: PydanticObjectId
    user_name: str
    content: str
    created_at: datetime = Field(default_factory=_utc_now)


class SharedList(Document):
    """A curated list of opportunities that can be shared publicly."""

    # Owner
    owner_id: Indexed(PydanticObjectId)
    owner_name: str

    # List metadata
    title: str
    slug: Indexed(str, unique=True)
    description: Optional[str] = None
    cover_image_url: Optional[str] = None

    # Visibility
    visibility: ListVisibility = "private"

    # Content
    opportunity_ids: List[PydanticObjectId] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)

    # Engagement
    view_count: int = 0
    like_count: int = 0
    liked_by: List[PydanticObjectId] = Field(default_factory=list)
    comments: List[ListComment] = Field(default_factory=list)

    # Featured/promoted
    is_featured: bool = False
    featured_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)

    class Settings:
        name = "shared_lists"
        indexes = [
            "owner_id",
            "visibility",
            "is_featured",
            "like_count",
            "created_at",
        ]

    def increment_views(self):
        """Increment view count."""
        self.view_count += 1

    def toggle_like(self, user_id: PydanticObjectId) -> bool:
        """Toggle like status for a user. Returns True if now liked."""
        if user_id in self.liked_by:
            self.liked_by.remove(user_id)
            self.like_count = max(0, self.like_count - 1)
            return False
        else:
            self.liked_by.append(user_id)
            self.like_count += 1
            return True

    def add_comment(self, user_id: PydanticObjectId, user_name: str, content: str):
        """Add a comment to the list."""
        self.comments.append(
            ListComment(
                user_id=user_id,
                user_name=user_name,
                content=content,
            )
        )
        self.updated_at = _utc_now()

    def add_opportunity(self, opportunity_id: PydanticObjectId):
        """Add an opportunity to the list."""
        if opportunity_id not in self.opportunity_ids:
            self.opportunity_ids.append(opportunity_id)
            self.updated_at = _utc_now()

    def remove_opportunity(self, opportunity_id: PydanticObjectId):
        """Remove an opportunity from the list."""
        if opportunity_id in self.opportunity_ids:
            self.opportunity_ids.remove(opportunity_id)
            self.updated_at = _utc_now()
