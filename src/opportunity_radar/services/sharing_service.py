"""Sharing and community service."""

import logging
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from beanie import PydanticObjectId
from openai import OpenAI

from ..config import get_settings
from ..models.shared_list import SharedList
from ..models.opportunity import Opportunity
from ..models.user import User

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    """Return current UTC time with timezone info."""
    return datetime.now(timezone.utc)


class SharingService:
    """Service for community sharing features."""

    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.base_url = settings.api_base_url

    def _create_slug(self, title: str, owner_id: str) -> str:
        """Create a unique slug for a list."""
        slug = title.lower()
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)
        slug = re.sub(r"[\s_]+", "-", slug)
        slug = re.sub(r"-+", "-", slug)
        slug = slug.strip("-")
        # Add part of owner ID for uniqueness
        return f"{slug}-{str(owner_id)[-6:]}"

    async def create_list(
        self,
        user: User,
        title: str,
        description: Optional[str] = None,
        visibility: str = "private",
        tags: List[str] = None,
        opportunity_ids: List[str] = None,
        cover_image_url: Optional[str] = None,
    ) -> SharedList:
        """Create a new shared list."""
        slug = self._create_slug(title, str(user.id))

        # Convert opportunity IDs
        opp_ids = []
        if opportunity_ids:
            for oid in opportunity_ids:
                try:
                    opp_ids.append(PydanticObjectId(oid))
                except Exception:
                    logger.warning(f"Invalid opportunity ID: {oid}")

        shared_list = SharedList(
            owner_id=user.id,
            owner_name=user.full_name or user.email.split("@")[0],
            title=title,
            slug=slug,
            description=description,
            visibility=visibility,
            tags=tags or [],
            opportunity_ids=opp_ids,
            cover_image_url=cover_image_url,
        )

        await shared_list.insert()
        logger.info(f"Created shared list: {shared_list.id} by {user.email}")

        return shared_list

    async def get_list(self, list_id: PydanticObjectId) -> Optional[SharedList]:
        """Get a shared list by ID."""
        return await SharedList.get(list_id)

    async def get_list_by_slug(self, slug: str) -> Optional[SharedList]:
        """Get a shared list by slug."""
        return await SharedList.find_one({"slug": slug})

    async def get_user_lists(
        self,
        user_id: PydanticObjectId,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[SharedList], int]:
        """Get all lists owned by a user."""
        query = SharedList.find({"owner_id": user_id})
        total = await query.count()
        lists = await query.sort("-created_at").skip(skip).limit(limit).to_list()
        return lists, total

    async def get_public_lists(
        self,
        skip: int = 0,
        limit: int = 20,
        tags: Optional[List[str]] = None,
        sort_by: str = "created_at",
    ) -> tuple[List[SharedList], int]:
        """Get public lists with optional filtering."""
        query_filter = {"visibility": "public"}

        if tags:
            query_filter["tags"] = {"$in": tags}

        query = SharedList.find(query_filter)
        total = await query.count()

        # Sort options
        sort_field = "-like_count" if sort_by == "popular" else "-created_at"
        lists = await query.sort(sort_field).skip(skip).limit(limit).to_list()

        return lists, total

    async def get_featured_lists(
        self,
        limit: int = 10,
    ) -> List[SharedList]:
        """Get featured lists."""
        return await SharedList.find(
            {"visibility": "public", "is_featured": True}
        ).sort("-featured_at").limit(limit).to_list()

    async def update_list(
        self,
        shared_list: SharedList,
        data: Dict[str, Any],
    ) -> SharedList:
        """Update a shared list."""
        for key, value in data.items():
            if value is not None and hasattr(shared_list, key):
                setattr(shared_list, key, value)

        shared_list.updated_at = _utc_now()
        await shared_list.save()

        return shared_list

    async def delete_list(self, shared_list: SharedList) -> None:
        """Delete a shared list."""
        await shared_list.delete()
        logger.info(f"Deleted shared list: {shared_list.id}")

    async def add_opportunity_to_list(
        self,
        shared_list: SharedList,
        opportunity_id: PydanticObjectId,
    ) -> SharedList:
        """Add an opportunity to a list."""
        shared_list.add_opportunity(opportunity_id)
        await shared_list.save()
        return shared_list

    async def remove_opportunity_from_list(
        self,
        shared_list: SharedList,
        opportunity_id: PydanticObjectId,
    ) -> SharedList:
        """Remove an opportunity from a list."""
        shared_list.remove_opportunity(opportunity_id)
        await shared_list.save()
        return shared_list

    async def toggle_like(
        self,
        shared_list: SharedList,
        user_id: PydanticObjectId,
    ) -> bool:
        """Toggle like on a list. Returns True if now liked."""
        is_liked = shared_list.toggle_like(user_id)
        await shared_list.save()
        return is_liked

    async def add_comment(
        self,
        shared_list: SharedList,
        user: User,
        content: str,
    ) -> SharedList:
        """Add a comment to a list."""
        user_name = user.full_name or user.email.split("@")[0]
        shared_list.add_comment(user.id, user_name, content)
        await shared_list.save()
        return shared_list

    async def record_view(self, shared_list: SharedList) -> None:
        """Record a view on a list."""
        shared_list.increment_views()
        await shared_list.save()

    async def get_list_opportunities(
        self,
        shared_list: SharedList,
    ) -> List[Opportunity]:
        """Get all opportunities in a list."""
        opportunities = []
        for opp_id in shared_list.opportunity_ids:
            opp = await Opportunity.get(opp_id)
            if opp:
                opportunities.append(opp)
        return opportunities

    def generate_share_url(self, shared_list: SharedList) -> str:
        """Generate a share URL for a list."""
        return f"{self.base_url}/lists/{shared_list.slug}"

    def generate_embed_code(self, shared_list: SharedList) -> str:
        """Generate an embed code for a list."""
        url = self.generate_share_url(shared_list)
        return f'<iframe src="{url}/embed" width="100%" height="400" frameborder="0"></iframe>'

    async def generate_list_description(
        self,
        shared_list: SharedList,
    ) -> str:
        """Use AI to generate a compelling description for a list."""
        opportunities = await self.get_list_opportunities(shared_list)

        if not opportunities:
            return "A curated collection of opportunities."

        opp_summaries = []
        for opp in opportunities[:10]:  # Limit to first 10
            summary = f"- {opp.title} ({opp.opportunity_type})"
            if opp.total_prize_value:
                summary += f" - ${opp.total_prize_value:,.0f}"
            opp_summaries.append(summary)

        prompt = f"""Generate a compelling 2-3 sentence description for a curated list titled "{shared_list.title}".

The list contains these opportunities:
{chr(10).join(opp_summaries)}

Tags: {', '.join(shared_list.tags) if shared_list.tags else 'None'}

Make the description engaging and highlight why this collection is valuable."""

        try:
            response = self.client.responses.create(
                model="gpt-5.2",
                input=prompt,
            )
            return response.output_text or "A curated collection of opportunities."
        except Exception as e:
            logger.error(f"Failed to generate description: {e}")
            return "A curated collection of opportunities."

    async def get_similar_lists(
        self,
        shared_list: SharedList,
        limit: int = 5,
    ) -> List[SharedList]:
        """Find similar public lists based on tags and opportunities."""
        if not shared_list.tags:
            return []

        similar = await SharedList.find(
            {
                "_id": {"$ne": shared_list.id},
                "visibility": "public",
                "tags": {"$in": shared_list.tags},
            }
        ).sort("-like_count").limit(limit).to_list()

        return similar


# Singleton instance
_sharing_service: Optional[SharingService] = None


def get_sharing_service() -> SharingService:
    """Get or create the sharing service singleton."""
    global _sharing_service
    if _sharing_service is None:
        _sharing_service = SharingService()
    return _sharing_service
