"""Profile repository for data access."""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.profile import Profile
from ..models.user import User

logger = logging.getLogger(__name__)


class ProfileRepository:
    """Repository for Profile CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, profile_id: str) -> Optional[Profile]:
        """Get profile by ID."""
        result = await self.db.execute(
            select(Profile).where(Profile.id == profile_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: str) -> Optional[Profile]:
        """Get profile by user ID."""
        result = await self.db.execute(
            select(Profile)
            .where(Profile.user_id == user_id)
            .options(selectinload(Profile.user))
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: str,
        profile_type: Optional[str] = None,
        stage: Optional[str] = None,
        tech_stack: Optional[list] = None,
        industries: Optional[list] = None,
        team_size: int = 1,
        availability_json: Optional[dict] = None,
        wins: Optional[list] = None,
        intents: Optional[list] = None,
        embedding: Optional[list] = None,
    ) -> Profile:
        """Create a new profile."""
        profile = Profile(
            user_id=user_id,
            profile_type=profile_type,
            stage=stage,
            tech_stack=tech_stack or [],
            industries=industries or [],
            team_size=team_size,
            availability_json=availability_json,
            wins=wins or [],
            intents=intents or [],
            embedding=embedding,
        )

        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)

        return profile

    async def update(
        self,
        profile: Profile,
        **kwargs,
    ) -> Profile:
        """Update profile fields."""
        for key, value in kwargs.items():
            if hasattr(profile, key) and value is not None:
                setattr(profile, key, value)

        await self.db.commit()
        await self.db.refresh(profile)

        return profile

    async def update_embedding(
        self,
        profile_id: str,
        embedding: list,
    ) -> Optional[Profile]:
        """Update profile embedding vector."""
        profile = await self.get_by_id(profile_id)
        if profile:
            profile.embedding = embedding
            await self.db.commit()
            await self.db.refresh(profile)
        return profile

    async def delete(self, profile_id: str) -> bool:
        """Delete a profile."""
        profile = await self.get_by_id(profile_id)
        if profile:
            await self.db.delete(profile)
            await self.db.commit()
            return True
        return False

    async def exists_for_user(self, user_id: str) -> bool:
        """Check if a profile exists for a user."""
        result = await self.db.execute(
            select(Profile.id).where(Profile.user_id == user_id)
        )
        return result.scalar_one_or_none() is not None
