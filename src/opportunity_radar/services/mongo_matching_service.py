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
    """Detailed breakdown of match score with multi-factor scoring."""

    # Similarity Scores (0-1)
    semantic_score: float = 0.0  # Semantic embedding similarity
    tech_overlap_score: float = 0.0  # Tech stack overlap
    industry_alignment_score: float = 0.0  # Industry/theme alignment
    goals_alignment_score: float = 0.0  # Goals matching

    # Timing Score (0-1)
    deadline_score: float = 0.0  # Penalize near deadlines

    # Eligibility (boolean, used for hard filtering)
    team_size_eligible: bool = True
    funding_stage_eligible: bool = True
    location_eligible: bool = True

    # Boost Factors
    track_record_boost: float = 0.0  # Past success indicators

    # Weights
    semantic_weight: float = 0.30
    tech_weight: float = 0.20
    industry_weight: float = 0.15
    goals_weight: float = 0.15
    deadline_weight: float = 0.10
    track_record_weight: float = 0.10

    @property
    def is_eligible(self) -> bool:
        """Check if all hard eligibility requirements are met."""
        return self.team_size_eligible and self.funding_stage_eligible and self.location_eligible

    @property
    def total_score(self) -> float:
        """Calculate weighted total score."""
        if not self.is_eligible:
            return 0.0

        base_score = (
            self.semantic_score * self.semantic_weight
            + self.tech_overlap_score * self.tech_weight
            + self.industry_alignment_score * self.industry_weight
            + self.goals_alignment_score * self.goals_weight
            + self.deadline_score * self.deadline_weight
            + self.track_record_boost * self.track_record_weight
        )
        return min(1.0, base_score)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "total": round(self.total_score, 3),
            "is_eligible": self.is_eligible,
            "factors": {
                "semantic": {
                    "score": round(self.semantic_score, 3),
                    "weight": self.semantic_weight,
                },
                "tech_overlap": {
                    "score": round(self.tech_overlap_score, 3),
                    "weight": self.tech_weight,
                },
                "industry_alignment": {
                    "score": round(self.industry_alignment_score, 3),
                    "weight": self.industry_weight,
                },
                "goals_alignment": {
                    "score": round(self.goals_alignment_score, 3),
                    "weight": self.goals_weight,
                },
                "deadline": {
                    "score": round(self.deadline_score, 3),
                    "weight": self.deadline_weight,
                },
                "track_record": {
                    "score": round(self.track_record_boost, 3),
                    "weight": self.track_record_weight,
                },
            },
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


# Goal to opportunity type mapping
GOAL_TYPE_MAPPING = {
    "funding": ["grant", "accelerator", "competition"],
    "prizes": ["hackathon", "competition", "bug-bounty", "bounty"],
    "learning": ["hackathon", "competition", "bootcamp"],
    "networking": ["hackathon", "accelerator", "conference"],
    "exposure": ["hackathon", "competition", "accelerator"],
    "mentorship": ["accelerator", "bootcamp"],
    "equity": ["accelerator"],
    "building": ["hackathon", "buildathon"],
}

# Funding stage to accelerator stage mapping
FUNDING_STAGE_MAPPING = {
    "bootstrapped": ["pre-seed", "idea", "early"],
    "pre_seed": ["pre-seed", "seed", "early"],
    "seed": ["seed", "early", "growth"],
    "series_a": ["series-a", "growth", "scaling"],
    "series_b_plus": ["growth", "scaling", "late"],
}


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
        """Compute match score between a profile and opportunity."""
        breakdown = MatchScoreBreakdown()
        match_reasons = []
        eligibility_issues = []
        suggestions = []
        matching_skills = []
        matching_themes = []
        warnings = []
        tips = []

        # 1. Apply hard filters (eligibility checks)
        self._apply_hard_filters(profile, opportunity, breakdown, eligibility_issues)

        # 2. Semantic similarity (embeddings)
        if profile.embedding and opportunity.embedding:
            breakdown.semantic_score = self._cosine_similarity(
                profile.embedding, opportunity.embedding
            )
            if breakdown.semantic_score > 0.75:
                match_reasons.append("Strong semantic alignment with your profile")
            elif breakdown.semantic_score > 0.6:
                match_reasons.append("Good semantic match")
        else:
            # Default to neutral if no embeddings
            breakdown.semantic_score = 0.5
            if not opportunity.embedding:
                suggestions.append("Opportunity lacks embedding - semantic matching unavailable")

        # 3. Tech stack overlap
        profile_tech = set(t.lower() for t in (profile.tech_stack or []))
        opp_tech = set(t.lower() for t in (opportunity.technologies or []))

        if profile_tech and opp_tech:
            overlap = profile_tech & opp_tech
            union = profile_tech | opp_tech
            breakdown.tech_overlap_score = len(overlap) / len(union) if union else 0.0
            matching_skills = list(overlap)[:5]

            if breakdown.tech_overlap_score > 0.5:
                match_reasons.append(f"Strong tech stack overlap: {', '.join(matching_skills[:3])}")
            elif breakdown.tech_overlap_score > 0.2:
                match_reasons.append("Some tech stack overlap")
            elif breakdown.tech_overlap_score == 0 and opp_tech:
                missing = list(opp_tech - profile_tech)[:3]
                tips.append(f"Consider learning: {', '.join(missing)}")
        else:
            breakdown.tech_overlap_score = 0.5  # Neutral if no tech requirements

        # 4. Industry/theme alignment
        profile_industries = set(i.lower() for i in (profile.interests or []))
        opp_themes = set(t.lower() for t in (opportunity.themes or []))

        if profile_industries and opp_themes:
            industry_overlap = profile_industries & opp_themes
            industry_union = profile_industries | opp_themes
            breakdown.industry_alignment_score = len(industry_overlap) / len(industry_union) if industry_union else 0.0
            matching_themes = list(industry_overlap)[:5]

            if breakdown.industry_alignment_score > 0.3:
                match_reasons.append(f"Industry alignment: {', '.join(matching_themes[:3])}")
        else:
            breakdown.industry_alignment_score = 0.5

        # 5. Goals alignment
        profile_goals = set(g.lower() for g in (profile.goals or []))
        opp_type = (opportunity.opportunity_type or "").lower()

        if profile_goals and opp_type:
            matching_goals = 0
            for goal in profile_goals:
                matching_types = GOAL_TYPE_MAPPING.get(goal, [])
                if opp_type in matching_types or any(t in opp_type for t in matching_types):
                    matching_goals += 1

            breakdown.goals_alignment_score = min(1.0, matching_goals / len(profile_goals)) if profile_goals else 0.5

            if breakdown.goals_alignment_score > 0.5:
                match_reasons.append("Aligns with your goals")
        else:
            breakdown.goals_alignment_score = 0.5

        # 6. Deadline score - encourage applying early
        breakdown.deadline_score = self._calculate_deadline_score(opportunity, warnings)

        # 7. Track record boost
        breakdown.track_record_boost = self._calculate_track_record_boost(profile, opportunity, tips)

        # Generate primary explanation
        primary_reason = self._generate_primary_reason(breakdown, match_reasons)

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

    def _calculate_deadline_score(
        self,
        opportunity: Opportunity,
        warnings: List[str],
    ) -> float:
        """Calculate deadline score - penalize near deadlines."""
        # Check timelines for deadline
        deadline = None
        if opportunity.timelines:
            for timeline in opportunity.timelines:
                if isinstance(timeline, dict):
                    deadline_str = timeline.get("submission_deadline") or timeline.get("registration_closes_at")
                    if deadline_str:
                        try:
                            deadline = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
                        except (ValueError, AttributeError):
                            pass
                        break

        if not deadline:
            return 0.7  # Neutral score if no deadline

        now = datetime.now(deadline.tzinfo) if deadline.tzinfo else datetime.utcnow()
        days_until = (deadline - now).days

        if days_until < 0:
            warnings.append("Deadline has passed")
            return 0.0
        elif days_until <= 1:
            warnings.append("Deadline TODAY!")
            return 0.3
        elif days_until <= 3:
            warnings.append(f"Deadline in {days_until} days")
            return 0.5
        elif days_until <= 7:
            warnings.append(f"Deadline in {days_until} days")
            return 0.7
        elif days_until <= 14:
            return 0.9
        else:
            return 1.0

    def _calculate_track_record_boost(
        self,
        profile: Profile,
        opportunity: Opportunity,
        tips: List[str],
    ) -> float:
        """Calculate boost based on track record."""
        boost = 0.0

        # Hackathon wins boost for hackathons
        if opportunity.opportunity_type == "hackathon" and profile.previous_hackathon_wins > 0:
            boost += min(0.3, profile.previous_hackathon_wins * 0.1)
            if profile.previous_hackathon_wins >= 3:
                tips.append("Your hackathon experience gives you an edge!")

        # Previous accelerator experience boost
        if opportunity.opportunity_type == "accelerator" and profile.previous_accelerators:
            boost += 0.2
            tips.append("Your accelerator experience is valuable here")

        # Notable achievements boost
        if profile.notable_achievements:
            boost += min(0.2, len(profile.notable_achievements) * 0.05)

        return min(1.0, boost)

    def _generate_primary_reason(
        self,
        breakdown: MatchScoreBreakdown,
        match_reasons: List[str],
    ) -> str:
        """Generate the primary match explanation."""
        if not breakdown.is_eligible:
            return "Not eligible based on requirements"

        if breakdown.total_score >= 0.8:
            if breakdown.tech_overlap_score > 0.6:
                return "Excellent tech stack match for your skills"
            elif breakdown.semantic_score > 0.7:
                return "Strong overall alignment with your profile"
            else:
                return "Great opportunity based on your goals"
        elif breakdown.total_score >= 0.6:
            if match_reasons:
                return match_reasons[0]
            return "Good match for your profile"
        elif breakdown.total_score >= 0.4:
            return "Moderate match - worth exploring"
        else:
            return "Partial match - some alignment with your profile"

    def _cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float],
    ) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            a = np.array(vec1)
            b = np.array(vec2)

            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)

            if norm_a == 0 or norm_b == 0:
                return 0.0

            similarity = dot_product / (norm_a * norm_b)
            # Normalize to 0-1 range (cosine similarity can be -1 to 1)
            return float((similarity + 1) / 2)
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
