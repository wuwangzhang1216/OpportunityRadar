"""Profile service for business logic."""

import logging
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.profile import Profile
from ..repositories.profile_repository import ProfileRepository
from ..services.embedding_service import get_embedding_service, EmbeddingService
from ..services.matching_service import MatchingService
from ..schemas.profile import ProfileCreate, ProfileUpdate, ProfileResponse, AvailabilityBlock

logger = logging.getLogger(__name__)


class ProfileService:
    """Service for profile-related operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = ProfileRepository(db)
        self._embedding_service: Optional[EmbeddingService] = None

    @property
    def embedding_service(self) -> EmbeddingService:
        """Lazy load embedding service."""
        if self._embedding_service is None:
            self._embedding_service = get_embedding_service()
        return self._embedding_service

    async def get_profile(self, profile_id: str) -> Optional[ProfileResponse]:
        """Get profile by ID."""
        profile = await self.repository.get_by_id(profile_id)
        if not profile:
            return None
        return self._to_response(profile)

    async def get_profile_by_user(self, user_id: str) -> Optional[ProfileResponse]:
        """Get profile by user ID."""
        profile = await self.repository.get_by_user_id(user_id)
        if not profile:
            return None
        return self._to_response(profile)

    async def create_profile(
        self,
        user_id: str,
        data: ProfileCreate,
        compute_matches: bool = True,
    ) -> ProfileResponse:
        """
        Create a new profile for a user.

        Args:
            user_id: The user ID
            data: Profile creation data
            compute_matches: Whether to compute matches after creation

        Returns:
            Created profile
        """
        # Check if profile already exists
        existing = await self.repository.get_by_user_id(user_id)
        if existing:
            raise ValueError("Profile already exists for this user")

        # Convert availability blocks to JSON
        availability_json = None
        if data.availability:
            availability_json = {
                "blocks": [
                    {"dow": b.dow, "start": b.start, "end": b.end}
                    for b in data.availability
                ]
            }

        # Generate embedding for the profile
        embedding = None
        try:
            embedding_text = self.embedding_service.create_profile_embedding_text(
                tech_stack=data.tech_stack,
                industries=data.industries,
                intents=data.intents,
                profile_type=data.profile_type,
                stage=data.stage,
            )
            embedding = self.embedding_service.get_embedding(embedding_text)
        except Exception as e:
            logger.warning(f"Failed to generate profile embedding: {e}")

        # Create profile
        profile = await self.repository.create(
            user_id=user_id,
            profile_type=data.profile_type,
            stage=data.stage,
            tech_stack=data.tech_stack,
            industries=data.industries,
            team_size=data.team_size,
            availability_json=availability_json,
            wins=data.wins,
            intents=data.intents,
            embedding=embedding,
        )

        # Compute initial matches
        if compute_matches:
            try:
                matching_service = MatchingService(self.db)
                matches = await matching_service.compute_matches_for_profile(profile.id)
                await matching_service.save_matches(profile.id, matches)
                logger.info(f"Computed {len(matches)} initial matches for profile {profile.id}")
            except Exception as e:
                logger.error(f"Failed to compute initial matches: {e}")

        return self._to_response(profile)

    async def update_profile(
        self,
        user_id: str,
        data: ProfileUpdate,
        recompute_matches: bool = True,
    ) -> Optional[ProfileResponse]:
        """
        Update a user's profile.

        Args:
            user_id: The user ID
            data: Profile update data
            recompute_matches: Whether to recompute matches after update

        Returns:
            Updated profile or None if not found
        """
        profile = await self.repository.get_by_user_id(user_id)
        if not profile:
            return None

        # Prepare update kwargs
        update_kwargs = {}

        if data.profile_type is not None:
            update_kwargs["profile_type"] = data.profile_type

        if data.stage is not None:
            update_kwargs["stage"] = data.stage

        if data.tech_stack is not None:
            update_kwargs["tech_stack"] = data.tech_stack

        if data.industries is not None:
            update_kwargs["industries"] = data.industries

        if data.team_size is not None:
            update_kwargs["team_size"] = data.team_size

        if data.wins is not None:
            update_kwargs["wins"] = data.wins

        if data.intents is not None:
            update_kwargs["intents"] = data.intents

        if data.availability is not None:
            update_kwargs["availability_json"] = {
                "blocks": [
                    {"dow": b.dow, "start": b.start, "end": b.end}
                    for b in data.availability
                ]
            }

        # Update profile
        profile = await self.repository.update(profile, **update_kwargs)

        # Regenerate embedding if relevant fields changed
        embedding_fields = {"tech_stack", "industries", "intents", "profile_type", "stage"}
        if embedding_fields & set(update_kwargs.keys()):
            try:
                embedding_text = self.embedding_service.create_profile_embedding_text(
                    tech_stack=profile.tech_stack or [],
                    industries=profile.industries or [],
                    intents=profile.intents or [],
                    profile_type=profile.profile_type,
                    stage=profile.stage,
                )
                embedding = self.embedding_service.get_embedding(embedding_text)
                await self.repository.update_embedding(profile.id, embedding)
            except Exception as e:
                logger.warning(f"Failed to update profile embedding: {e}")

        # Recompute matches
        if recompute_matches:
            try:
                matching_service = MatchingService(self.db)
                matches = await matching_service.compute_matches_for_profile(profile.id)
                await matching_service.save_matches(profile.id, matches)
                logger.info(f"Recomputed {len(matches)} matches for profile {profile.id}")
            except Exception as e:
                logger.error(f"Failed to recompute matches: {e}")

        return self._to_response(profile)

    async def update_availability(
        self,
        user_id: str,
        availability: List[AvailabilityBlock],
    ) -> Optional[ProfileResponse]:
        """Update profile availability only."""
        profile = await self.repository.get_by_user_id(user_id)
        if not profile:
            return None

        availability_json = {
            "blocks": [
                {"dow": b.dow, "start": b.start, "end": b.end}
                for b in availability
            ]
        }

        profile = await self.repository.update(
            profile, availability_json=availability_json
        )

        return self._to_response(profile)

    async def delete_profile(self, user_id: str) -> bool:
        """Delete a user's profile."""
        profile = await self.repository.get_by_user_id(user_id)
        if not profile:
            return False
        return await self.repository.delete(profile.id)

    def _to_response(self, profile: Profile) -> ProfileResponse:
        """Convert Profile model to response schema."""
        # Convert availability JSON back to blocks
        availability = []
        if profile.availability_json and "blocks" in profile.availability_json:
            for block in profile.availability_json["blocks"]:
                availability.append(
                    AvailabilityBlock(
                        dow=block["dow"],
                        start=block["start"],
                        end=block["end"],
                    )
                )

        return ProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            profile_type=profile.profile_type,
            stage=profile.stage,
            tech_stack=profile.tech_stack or [],
            industries=profile.industries or [],
            team_size=profile.team_size or 1,
            availability=availability,
            wins=profile.wins or [],
            intents=profile.intents or [],
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
