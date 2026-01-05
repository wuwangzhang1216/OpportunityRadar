"""MongoDB-based matching service for computing matches with embeddings.

This service uses MongoDB models (Beanie) for matching profiles with opportunities,
utilizing OpenAI embeddings for semantic similarity scoring with multi-factor scoring,
hard filters, and human-readable explanations.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np

from ..models.profile import Profile
from ..models.opportunity import Opportunity
from ..models.match import Match
from .embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


@dataclass
class MatchScoreBreakdown:
    """Simplified scoring: semantic similarity is the primary signal.

    The embedding vectors already encode tech stack, industries, goals, and description.
    Additional factors only provide minor adjustments for specific signals.
    """

    # Primary score: semantic embedding similarity (0-1)
    # This captures tech, industry, goals, and overall fit in one vector comparison
    semantic_score: float = 0.0

    # Secondary signals for specific adjustments
    recency_boost: float = 0.0      # Boost for recently posted opportunities
    popularity_boost: float = 0.0   # Boost based on participant count / engagement

    # Eligibility (hard filters)
    team_size_eligible: bool = True
    funding_stage_eligible: bool = True
    location_eligible: bool = True

    @property
    def is_eligible(self) -> bool:
        """Check if all hard eligibility requirements are met."""
        return self.team_size_eligible and self.funding_stage_eligible and self.location_eligible

    @property
    def total_score(self) -> float:
        """Score is primarily semantic similarity with minor boosts."""
        if not self.is_eligible:
            return 0.0

        # Base score is semantic similarity (already 0-1)
        # Apply minor boosts (max 5% total boost)
        boost = min(0.05, self.recency_boost + self.popularity_boost)

        return min(1.0, self.semantic_score + boost)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "total": round(self.total_score, 3),
            "is_eligible": self.is_eligible,
            "semantic_score": round(self.semantic_score, 3),
            "recency_boost": round(self.recency_boost, 3),
            "popularity_boost": round(self.popularity_boost, 3),
            "eligibility": {
                "team_size": self.team_size_eligible,
                "funding_stage": self.funding_stage_eligible,
                "location": self.location_eligible,
            },
        }


@dataclass
class MatchExplanation:
    """Human-readable match explanation."""

    primary_reason: str
    matching_skills: List[str] = field(default_factory=list)
    matching_themes: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    tips: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "primary_reason": self.primary_reason,
            "matching_skills": self.matching_skills,
            "matching_themes": self.matching_themes,
            "warnings": self.warnings,
            "tips": self.tips,
        }


@dataclass
class MatchResult:
    """Result of matching a profile to an opportunity."""

    opportunity_id: str
    score: float
    breakdown: MatchScoreBreakdown
    explanation: MatchExplanation
    match_reasons: List[str] = field(default_factory=list)
    eligibility_issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


# Industry/theme aliases for fuzzy matching (used for display only)
INDUSTRY_ALIASES = {
    "ai": ["ai/ml", "machine learning/ai", "machine learning", "artificial intelligence", "ml", "deep learning", "llm"],
    "ml": ["ai/ml", "machine learning/ai", "machine learning", "ml", "ai"],
    "developer tools": ["devtools", "dev tools", "developer", "tools"],
    "data visualization": ["data viz", "visualization", "data", "analytics"],
    "fintech": ["finance", "financial", "banking", "payments"],
    "healthtech": ["health", "healthcare", "medical", "biotech"],
    "edtech": ["education", "learning", "e-learning"],
    "saas": ["software", "cloud", "enterprise"],
    "productivity": ["productivity", "workflow", "automation"],
    "web": ["web", "web development", "frontend", "backend"],
}


def fuzzy_industry_match(profile_industries: set, opp_themes: set) -> tuple[float, list]:
    """
    Compute fuzzy industry/theme match score.

    Returns:
        Tuple of (score, list of matching themes)
    """
    if not profile_industries or not opp_themes:
        return 0.5, []

    matches = set()

    # Direct matches
    direct_overlap = profile_industries & opp_themes
    matches.update(direct_overlap)

    # Fuzzy matches using aliases
    for profile_ind in profile_industries:
        profile_lower = profile_ind.lower()
        # Check if profile industry has aliases
        for alias_key, alias_values in INDUSTRY_ALIASES.items():
            if profile_lower in alias_values or alias_key in profile_lower:
                # Check if any opportunity theme matches these aliases
                for opp_theme in opp_themes:
                    opp_lower = opp_theme.lower()
                    if opp_lower in alias_values or alias_key in opp_lower:
                        matches.add(opp_theme)
                        break

    # Also do substring matching for partial matches
    for profile_ind in profile_industries:
        profile_lower = profile_ind.lower()
        for opp_theme in opp_themes:
            opp_lower = opp_theme.lower()
            # Check if one contains the other (partial match)
            if profile_lower in opp_lower or opp_lower in profile_lower:
                matches.add(opp_theme)

    if not matches:
        return 0.0, []

    # Score based on how many profile industries found matches
    score = min(1.0, len(matches) / len(profile_industries))
    return score, list(matches)


class MongoMatchingService:
    """Service for computing matches using MongoDB models with embeddings."""

    def __init__(self):
        self._embedding_service = None

    @property
    def embedding_service(self):
        """Lazy load embedding service."""
        if self._embedding_service is None:
            self._embedding_service = get_embedding_service()
        return self._embedding_service

    async def compute_matches_for_profile(
        self,
        profile_id: str,
        limit: int = 50,
        min_score: float = 0.3,
        only_active: bool = True,
        apply_hard_filters: bool = True,
    ) -> List[MatchResult]:
        """
        Compute matches for a profile against all active opportunities.

        Args:
            profile_id: The profile ID (MongoDB ObjectId as string)
            limit: Maximum number of matches to return
            min_score: Minimum score threshold
            only_active: Only match against active opportunities
            apply_hard_filters: Apply team size, eligibility filters

        Returns:
            List of match results sorted by score
        """
        from beanie import PydanticObjectId

        # Get profile
        try:
            profile = await Profile.get(PydanticObjectId(profile_id))
        except Exception as e:
            logger.error(f"Failed to get profile {profile_id}: {e}")
            return []

        if not profile:
            logger.warning(f"Profile {profile_id} not found")
            return []

        # Build opportunity query
        query = {}
        if only_active:
            query["is_active"] = True

        # Get opportunities
        opportunities = await Opportunity.find(query).to_list()

        if not opportunities:
            logger.info("No opportunities found for matching")
            return []

        # Compute matches with yield points to prevent event loop blocking
        matches = []
        for i, opp in enumerate(opportunities):
            # Yield every 50 opportunities to allow other async tasks to run
            if i > 0 and i % 50 == 0:
                await asyncio.sleep(0)

            result = self._compute_single_match(profile, opp)

            # Apply hard filters
            if apply_hard_filters and not result.breakdown.is_eligible:
                continue

            if result.score >= min_score:
                matches.append(result)

        # Sort by score descending
        matches.sort(key=lambda m: m.score, reverse=True)

        return matches[:limit]

    def _compute_single_match(
        self,
        profile: Profile,
        opportunity: Opportunity,
    ) -> MatchResult:
        """Compute match score using semantic similarity as the primary signal.

        The embedding vectors already encode:
        - Tech stack (profile.tech_stack vs opportunity.technologies)
        - Industries/themes (profile.interests vs opportunity.themes)
        - Goals alignment (profile.goals vs opportunity.opportunity_type)
        - Overall description fit (profile.bio vs opportunity.description)

        So we rely on cosine similarity between embeddings rather than
        naive string matching.
        """
        breakdown = MatchScoreBreakdown()
        match_reasons = []
        eligibility_issues = []
        suggestions = []
        warnings = []
        tips = []

        # 1. Apply hard filters (eligibility checks)
        self._apply_hard_filters(profile, opportunity, breakdown, eligibility_issues)

        # 2. Semantic similarity - THE PRIMARY SCORE
        if profile.embedding and opportunity.embedding:
            breakdown.semantic_score = self._cosine_similarity(
                profile.embedding, opportunity.embedding
            )

            # Generate match reasons based on score
            if breakdown.semantic_score >= 0.80:
                match_reasons.append("Excellent match for your profile")
            elif breakdown.semantic_score >= 0.75:
                match_reasons.append("Strong alignment with your skills and interests")
            elif breakdown.semantic_score >= 0.70:
                match_reasons.append("Good match based on your profile")
            elif breakdown.semantic_score >= 0.65:
                match_reasons.append("Moderate fit - worth exploring")
        else:
            breakdown.semantic_score = 0.5
            if not opportunity.embedding:
                suggestions.append("Opportunity data incomplete")

        # 3. Recency boost - newer opportunities get slight boost
        if opportunity.created_at:
            days_old = (datetime.utcnow() - opportunity.created_at).days
            if days_old <= 7:
                breakdown.recency_boost = 0.02  # 2% boost for week-old
            elif days_old <= 14:
                breakdown.recency_boost = 0.01  # 1% boost for 2 weeks

        # 4. Popularity boost - based on participant count if available
        if opportunity.participant_count and opportunity.participant_count > 100:
            breakdown.popularity_boost = 0.01  # 1% boost for popular events

        # Generate explanation
        primary_reason = self._generate_explanation(breakdown, match_reasons)

        # Extract matching themes/skills for display (informational only, not used in scoring)
        matching_themes = self._find_matching_themes(profile, opportunity)
        matching_skills = self._find_matching_skills(profile, opportunity)

        explanation = MatchExplanation(
            primary_reason=primary_reason,
            matching_skills=matching_skills,
            matching_themes=matching_themes,
            warnings=warnings,
            tips=tips,
        )

        return MatchResult(
            opportunity_id=str(opportunity.id),
            score=breakdown.total_score,
            breakdown=breakdown,
            explanation=explanation,
            match_reasons=match_reasons,
            eligibility_issues=eligibility_issues,
            suggestions=suggestions,
        )

    def _find_matching_themes(self, profile: Profile, opportunity: Opportunity) -> List[str]:
        """Find matching themes for display purposes (not scoring)."""
        profile_interests = set(i.lower() for i in (profile.interests or []))
        opp_themes = set(t.lower() for t in (opportunity.themes or []))

        # Use fuzzy matching for display
        _, matches = fuzzy_industry_match(profile_interests, opp_themes)
        return matches[:3]

    def _find_matching_skills(self, profile: Profile, opportunity: Opportunity) -> List[str]:
        """Find matching skills for display purposes (not scoring)."""
        profile_tech = set(t.lower() for t in (profile.tech_stack or []))
        opp_tech = set(t.lower() for t in (opportunity.technologies or []))
        return list(profile_tech & opp_tech)[:3]

    def _generate_explanation(self, breakdown: MatchScoreBreakdown, reasons: List[str]) -> str:
        """Generate primary explanation based on score."""
        if not breakdown.is_eligible:
            return "Not eligible based on requirements"

        if reasons:
            return reasons[0]

        score = breakdown.total_score
        if score >= 0.80:
            return "Excellent match for your profile"
        elif score >= 0.70:
            return "Good match based on your interests"
        elif score >= 0.60:
            return "Worth exploring"
        else:
            return "Some alignment with your profile"

    def _apply_hard_filters(
        self,
        profile: Profile,
        opportunity: Opportunity,
        breakdown: MatchScoreBreakdown,
        eligibility_issues: List[str],
    ) -> None:
        """Apply hard eligibility filters."""
        # Team size check
        profile_team_size = profile.team_size or 1
        if opportunity.team_size_min and profile_team_size < opportunity.team_size_min:
            breakdown.team_size_eligible = False
            eligibility_issues.append(
                f"Team size too small: need {opportunity.team_size_min}, have {profile_team_size}"
            )
        if opportunity.team_size_max and profile_team_size > opportunity.team_size_max:
            breakdown.team_size_eligible = False
            eligibility_issues.append(
                f"Team size too large: max {opportunity.team_size_max}, have {profile_team_size}"
            )

        # Funding stage check for accelerators
        if opportunity.opportunity_type == "accelerator" and profile.funding_stage:
            # Most accelerators have stage requirements - this is simplified
            breakdown.funding_stage_eligible = True  # Default to eligible

        # Location check (simplified - would need opportunity location requirements)
        breakdown.location_eligible = True

    def _cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float],
    ) -> float:
        """Calculate cosine similarity between two vectors with score spreading.

        OpenAI embeddings typically produce similarities in 0.3-0.5 range for
        related content (after normalization). We apply a transformation to
        spread scores more visually meaningful across the 0-1 range.
        """
        try:
            a = np.array(vec1)
            b = np.array(vec2)

            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)

            if norm_a == 0 or norm_b == 0:
                return 0.0

            # Raw cosine similarity (typically 0.3-0.5 for related embeddings)
            raw_similarity = dot_product / (norm_a * norm_b)

            # Apply score spreading transformation:
            # Map typical range [0.25, 0.55] to [0.50, 0.95] for better user perception
            # This makes scores more meaningful (50% = weak, 70% = good, 90% = excellent)
            min_raw = 0.25  # Minimum expected similarity for any content
            max_raw = 0.55  # Maximum typical similarity for highly relevant content
            min_output = 0.50
            max_output = 0.95

            if raw_similarity <= min_raw:
                stretched = raw_similarity / min_raw * min_output
            elif raw_similarity >= max_raw:
                stretched = max_output + (raw_similarity - max_raw) * 0.5
            else:
                # Linear interpolation in the typical range
                ratio = (raw_similarity - min_raw) / (max_raw - min_raw)
                stretched = min_output + ratio * (max_output - min_output)

            return float(max(0.0, min(1.0, stretched)))
        except Exception as e:
            logger.warning(f"Error calculating cosine similarity: {e}")
            return 0.5

    async def save_matches(
        self,
        user_id: str,
        match_results: List[MatchResult],
    ) -> int:
        """
        Save computed matches to database.

        Cleans up stale matches (non-bookmarked, non-dismissed) that are no longer
        in the computed results, while preserving user actions (bookmarks/dismissals).

        Args:
            user_id: The user ID
            match_results: List of match results to save

        Returns:
            Number of matches saved/updated
        """
        from beanie import PydanticObjectId
        from beanie.operators import In, NotIn

        count = 0
        user_oid = PydanticObjectId(user_id)

        # Get the opportunity IDs from new match results
        new_opp_ids = {PydanticObjectId(r.opportunity_id) for r in match_results}

        # Clean up stale matches: remove matches for opportunities no longer in results
        # BUT preserve bookmarked and dismissed matches (user actions should persist)
        if new_opp_ids:
            await Match.find(
                Match.user_id == user_oid,
                NotIn(Match.opportunity_id, list(new_opp_ids)),
                Match.is_bookmarked == False,
                Match.is_dismissed == False,
            ).delete()
        else:
            # If no new matches, still clean up non-actioned matches
            await Match.find(
                Match.user_id == user_oid,
                Match.is_bookmarked == False,
                Match.is_dismissed == False,
            ).delete()

        for result in match_results:
            opp_oid = PydanticObjectId(result.opportunity_id)

            # Check if match exists
            existing = await Match.find_one(
                Match.user_id == user_oid,
                Match.opportunity_id == opp_oid,
            )

            if existing:
                # Update existing match
                existing.overall_score = result.score
                existing.semantic_score = result.breakdown.semantic_score
                existing.score_breakdown = result.breakdown.to_dict()
                existing.eligibility_status = "eligible" if result.breakdown.is_eligible else "ineligible"
                existing.eligibility_issues = result.eligibility_issues
                existing.fix_suggestions = result.suggestions + result.explanation.tips
                existing.updated_at = datetime.utcnow()
                await existing.save()
            else:
                # Create new match
                match = Match(
                    user_id=user_oid,
                    opportunity_id=opp_oid,
                    overall_score=result.score,
                    semantic_score=result.breakdown.semantic_score,
                    score_breakdown=result.breakdown.to_dict(),
                    eligibility_status="eligible" if result.breakdown.is_eligible else "ineligible",
                    eligibility_issues=result.eligibility_issues,
                    fix_suggestions=result.suggestions + result.explanation.tips,
                )
                await match.insert()
                count += 1

        # Update profile's last_match_computation timestamp
        profile = await Profile.find_one(Profile.user_id == user_oid)
        if profile:
            profile.last_match_computation = datetime.utcnow()
            await profile.save()

        return count

    async def get_top_matches_for_user(
        self,
        user_id: str,
        limit: int = 20,
        include_dismissed: bool = False,
    ) -> List[Dict]:
        """
        Get top matches for a user with opportunity details.

        Args:
            user_id: The user ID
            limit: Number of matches to return
            include_dismissed: Whether to include dismissed matches

        Returns:
            List of match dictionaries with opportunity details
        """
        from beanie import PydanticObjectId

        user_oid = PydanticObjectId(user_id)

        query = Match.find(Match.user_id == user_oid)

        if not include_dismissed:
            query = query.find(Match.is_dismissed == False)  # noqa: E712

        matches = await query.sort("-overall_score").limit(limit).to_list()

        results = []
        for match in matches:
            opp = await Opportunity.get(match.opportunity_id)
            results.append({
                "id": str(match.id),
                "score": match.overall_score,
                "score_breakdown": match.score_breakdown,
                "is_bookmarked": match.is_bookmarked,
                "is_dismissed": match.is_dismissed,
                "eligibility_status": match.eligibility_status,
                "eligibility_issues": match.eligibility_issues,
                "suggestions": match.fix_suggestions,
                "created_at": match.created_at.isoformat() if match.created_at else None,
                "opportunity": {
                    "id": str(opp.id) if opp else None,
                    "title": opp.title if opp else None,
                    "type": opp.opportunity_type if opp else None,
                    "logo_url": opp.logo_url if opp else None,
                    "website_url": opp.website_url if opp else None,
                    "themes": opp.themes if opp else [],
                    "technologies": opp.technologies if opp else [],
                    "total_prize_value": opp.total_prize_value if opp else None,
                    "format": opp.format if opp else None,
                } if opp else None,
            })

        return results

    async def bookmark_match(self, user_id: str, opportunity_id: str) -> bool:
        """Bookmark a match."""
        from beanie import PydanticObjectId

        match = await Match.find_one(
            Match.user_id == PydanticObjectId(user_id),
            Match.opportunity_id == PydanticObjectId(opportunity_id),
        )

        if match:
            match.is_bookmarked = True
            match.updated_at = datetime.utcnow()
            await match.save()
            return True
        return False

    async def dismiss_match(self, user_id: str, opportunity_id: str) -> bool:
        """Dismiss a match."""
        from beanie import PydanticObjectId

        match = await Match.find_one(
            Match.user_id == PydanticObjectId(user_id),
            Match.opportunity_id == PydanticObjectId(opportunity_id),
        )

        if match:
            match.is_dismissed = True
            match.updated_at = datetime.utcnow()
            await match.save()
            return True
        return False

    async def record_feedback(
        self,
        user_id: str,
        opportunity_id: str,
        action: str,
    ) -> bool:
        """
        Record user feedback for match learning.

        Args:
            user_id: User ID
            opportunity_id: Opportunity ID
            action: One of 'bookmark', 'pipeline', 'apply', 'dismiss', 'view'

        Returns:
            True if feedback was recorded
        """
        from beanie import PydanticObjectId

        match = await Match.find_one(
            Match.user_id == PydanticObjectId(user_id),
            Match.opportunity_id == PydanticObjectId(opportunity_id),
        )

        if not match:
            return False

        # Update match based on action
        if action == "bookmark":
            match.is_bookmarked = True
        elif action == "dismiss":
            match.is_dismissed = True
        elif action == "apply":
            match.is_bookmarked = True  # Auto-bookmark when applied

        match.updated_at = datetime.utcnow()
        await match.save()

        # In future: use feedback to adjust scoring for similar opportunities
        logger.info(f"Recorded feedback: user={user_id}, opp={opportunity_id}, action={action}")

        return True


# Singleton instance
_mongo_matching_service: Optional[MongoMatchingService] = None


def get_mongo_matching_service() -> MongoMatchingService:
    """Get or create the MongoDB matching service singleton."""
    global _mongo_matching_service
    if _mongo_matching_service is None:
        _mongo_matching_service = MongoMatchingService()
    return _mongo_matching_service


async def recompute_all_matches_mongo() -> Dict:
    """
    Recompute matches for all profiles using MongoDB.

    Returns:
        Statistics about the recomputation
    """
    service = get_mongo_matching_service()

    profiles = await Profile.find_all().to_list()

    stats = {
        "profiles_processed": 0,
        "total_matches": 0,
        "errors": 0,
    }

    for profile in profiles:
        try:
            matches = await service.compute_matches_for_profile(str(profile.id))
            await service.save_matches(str(profile.user_id), matches)

            stats["profiles_processed"] += 1
            stats["total_matches"] += len(matches)
        except Exception as e:
            logger.error(f"Error computing matches for profile {profile.id}: {e}")
            stats["errors"] += 1

    return stats
