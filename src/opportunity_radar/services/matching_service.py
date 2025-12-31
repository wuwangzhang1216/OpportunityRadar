"""Matching service for computing and storing matches."""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.match import Match
from ..models.profile import Profile
from ..models.opportunity import Opportunity
from ..models.batch import Batch
from ..matching.dsl_engine import ProfileContext, OpportunityContext, get_dsl_engine
from ..matching.scorer import MatchingScorer, MatchResult, get_scorer
from ..services.embedding_service import get_embedding_service
from ..schemas.match import MatchResponse

logger = logging.getLogger(__name__)


class MatchingService:
    """Service for computing and managing matches."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.scorer = get_scorer()

    async def compute_matches_for_profile(
        self,
        profile_id: str,
        limit: int = 50,
        min_score: float = 0.3,
    ) -> List[MatchResult]:
        """
        Compute matches for a profile against all active opportunities.

        Args:
            profile_id: The profile to match
            limit: Maximum number of matches to return
            min_score: Minimum score threshold

        Returns:
            List of match results sorted by score
        """
        # Get profile with embedding
        profile = await self._get_profile(profile_id)
        if not profile:
            return []

        # Get active batches with opportunities
        batches = await self._get_active_batches()

        # Build profile context
        profile_context = ProfileContext(
            profile_type=profile.profile_type,
            stage=profile.stage,
            tech_stack=profile.tech_stack or [],
            industries=profile.industries or [],
            team_size=profile.team_size or 1,
            is_student=profile.profile_type == "student",
        )

        matches = []

        for batch in batches:
            opportunity = batch.opportunity
            if not opportunity:
                continue

            # Build opportunity context
            opp_context = OpportunityContext(
                regions=batch.regions or [],
                team_min=batch.team_min,
                team_max=batch.team_max,
                student_only=batch.student_only or False,
                remote_ok=batch.remote_ok if batch.remote_ok is not None else True,
            )

            # Get deadline from timeline
            deadline = None
            event_start = None
            event_end = None
            if batch.timeline:
                deadline = batch.timeline.submission_deadline or batch.timeline.registration_closes_at
                event_start = batch.timeline.event_starts_at
                event_end = batch.timeline.event_ends_at

            # Calculate match
            result = self.scorer.calculate_match(
                profile_context=profile_context,
                opportunity_context=opp_context,
                opportunity_id=opportunity.id,
                batch_id=batch.id,
                profile_embedding=profile.embedding,
                opportunity_embedding=None,  # TODO: Add opportunity embeddings
                deadline=deadline,
                event_start=event_start,
                event_end=event_end,
                opportunity_category=opportunity.category,
                profile_intents=profile.intents,
            )

            if result.score >= min_score:
                matches.append(result)

        # Sort by score descending
        matches.sort(key=lambda m: m.score, reverse=True)

        return matches[:limit]

    async def save_matches(
        self,
        profile_id: str,
        match_results: List[MatchResult],
    ) -> int:
        """
        Save computed matches to database.

        Args:
            profile_id: The profile ID
            match_results: List of match results to save

        Returns:
            Number of matches saved
        """
        count = 0

        for result in match_results:
            # Check if match already exists
            existing = await self.db.execute(
                select(Match).where(
                    and_(
                        Match.profile_id == profile_id,
                        Match.batch_id == result.batch_id,
                    )
                )
            )
            existing_match = existing.scalar_one_or_none()

            if existing_match:
                # Update existing match
                existing_match.score = result.score
                existing_match.score_breakdown = result.breakdown.to_dict()
                existing_match.reasons_json = {
                    "match_reasons": result.match_reasons,
                    "fail_reasons": result.reasons,
                    "suggestions": result.suggestions,
                }
            else:
                # Create new match
                match = Match(
                    profile_id=profile_id,
                    batch_id=result.batch_id,
                    score=result.score,
                    score_breakdown=result.breakdown.to_dict(),
                    reasons_json={
                        "match_reasons": result.match_reasons,
                        "fail_reasons": result.reasons,
                        "suggestions": result.suggestions,
                    },
                    status="pending",
                )
                self.db.add(match)
                count += 1

        await self.db.commit()
        return count

    async def get_top_matches(
        self,
        profile_id: str,
        limit: int = 10,
        status: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get top matches for a profile.

        Args:
            profile_id: The profile ID
            limit: Number of matches to return
            status: Optional status filter

        Returns:
            List of match dictionaries with opportunity details
        """
        query = (
            select(Match)
            .options(
                selectinload(Match.batch).selectinload(Batch.opportunity),
                selectinload(Match.batch).selectinload(Batch.timeline),
            )
            .where(Match.profile_id == profile_id)
            .order_by(desc(Match.score))
            .limit(limit)
        )

        if status:
            query = query.where(Match.status == status)

        result = await self.db.execute(query)
        matches = result.scalars().all()

        return [self._match_to_dict(m) for m in matches]

    async def get_matches_for_profile(
        self,
        profile_id: str,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> Tuple[List[Dict], int]:
        """
        Get paginated matches for a profile.

        Args:
            profile_id: The profile ID
            skip: Number of records to skip
            limit: Number of records to return
            status: Optional status filter

        Returns:
            Tuple of (matches, total_count)
        """
        # Base query
        base_query = select(Match).where(Match.profile_id == profile_id)

        if status:
            base_query = base_query.where(Match.status == status)

        # Count total
        from sqlalchemy import func
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = (
            base_query
            .options(
                selectinload(Match.batch).selectinload(Batch.opportunity),
                selectinload(Match.batch).selectinload(Batch.timeline),
            )
            .order_by(desc(Match.score))
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        matches = result.scalars().all()

        return [self._match_to_dict(m) for m in matches], total

    async def update_match_status(
        self,
        profile_id: str,
        batch_id: str,
        status: str,
    ) -> Optional[Match]:
        """
        Update match status (interested, applied, dismissed).

        Args:
            profile_id: The profile ID
            batch_id: The batch ID
            status: New status

        Returns:
            Updated match or None if not found
        """
        result = await self.db.execute(
            select(Match).where(
                and_(
                    Match.profile_id == profile_id,
                    Match.batch_id == batch_id,
                )
            )
        )
        match = result.scalar_one_or_none()

        if match:
            match.status = status
            await self.db.commit()

        return match

    async def dismiss_match(self, profile_id: str, batch_id: str) -> bool:
        """Dismiss a match."""
        match = await self.update_match_status(profile_id, batch_id, "dismissed")
        return match is not None

    async def mark_interested(self, profile_id: str, batch_id: str) -> bool:
        """Mark a match as interested."""
        match = await self.update_match_status(profile_id, batch_id, "interested")
        return match is not None

    async def _get_profile(self, profile_id: str) -> Optional[Profile]:
        """Get profile by ID."""
        result = await self.db.execute(
            select(Profile).where(Profile.id == profile_id)
        )
        return result.scalar_one_or_none()

    async def _get_active_batches(self) -> List[Batch]:
        """Get all active batches with upcoming deadlines."""
        now = datetime.now()

        result = await self.db.execute(
            select(Batch)
            .options(
                selectinload(Batch.opportunity),
                selectinload(Batch.timeline),
            )
            .where(
                or_(
                    Batch.status == "upcoming",
                    Batch.status == "active",
                    Batch.status == "open",
                )
            )
        )

        return list(result.scalars().all())

    def _match_to_dict(self, match: Match) -> Dict:
        """Convert Match model to dictionary with opportunity details."""
        batch = match.batch
        opportunity = batch.opportunity if batch else None
        timeline = batch.timeline if batch else None

        return {
            "id": match.id,
            "score": match.score,
            "score_breakdown": match.score_breakdown,
            "status": match.status,
            "reasons": match.reasons_json or {},
            "created_at": match.created_at.isoformat() if match.created_at else None,
            "opportunity": {
                "id": opportunity.id if opportunity else None,
                "title": opportunity.title if opportunity else None,
                "category": opportunity.category if opportunity else None,
                "source": opportunity.source if opportunity else None,
                "url": opportunity.url if opportunity else None,
                "image_url": opportunity.image_url if opportunity else None,
            } if opportunity else None,
            "batch": {
                "id": batch.id if batch else None,
                "year": batch.year if batch else None,
                "season": batch.season if batch else None,
                "remote_ok": batch.remote_ok if batch else None,
                "deadline": timeline.submission_deadline.isoformat() if timeline and timeline.submission_deadline else None,
                "event_starts_at": timeline.event_starts_at.isoformat() if timeline and timeline.event_starts_at else None,
            } if batch else None,
        }


async def recompute_all_matches(db: AsyncSession) -> Dict:
    """
    Recompute matches for all profiles.
    Useful for batch processing or when scoring algorithm changes.
    """
    service = MatchingService(db)

    result = await db.execute(select(Profile))
    profiles = result.scalars().all()

    stats = {
        "profiles_processed": 0,
        "total_matches": 0,
    }

    for profile in profiles:
        matches = await service.compute_matches_for_profile(profile.id)
        await service.save_matches(profile.id, matches)

        stats["profiles_processed"] += 1
        stats["total_matches"] += len(matches)

    return stats
