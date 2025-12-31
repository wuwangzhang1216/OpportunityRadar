"""Multi-factor scoring engine for opportunity matching.

Scoring factors:
1. Semantic similarity (profile embedding vs opportunity embedding)
2. Eligibility rules (DSL engine)
3. Time fit (deadline proximity, event duration)
4. Team fit (size requirements)
5. Intent alignment (goals match opportunity type)
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np

from .dsl_engine import DSLEngine, EvaluationResult, ProfileContext, OpportunityContext

logger = logging.getLogger(__name__)


@dataclass
class ScoreBreakdown:
    """Detailed breakdown of matching score."""

    semantic_score: float = 0.0  # 0-1
    eligibility_score: float = 0.0  # 0-1
    time_score: float = 0.0  # 0-1
    team_score: float = 0.0  # 0-1
    intent_score: float = 0.0  # 0-1

    # Weights for each factor
    semantic_weight: float = 0.35
    eligibility_weight: float = 0.25
    time_weight: float = 0.15
    team_weight: float = 0.10
    intent_weight: float = 0.15

    @property
    def total_score(self) -> float:
        """Calculate weighted total score."""
        return (
            self.semantic_score * self.semantic_weight
            + self.eligibility_score * self.eligibility_weight
            + self.time_score * self.time_weight
            + self.team_score * self.team_weight
            + self.intent_score * self.intent_weight
        )

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "total": round(self.total_score, 3),
            "factors": {
                "semantic": {
                    "score": round(self.semantic_score, 3),
                    "weight": self.semantic_weight,
                },
                "eligibility": {
                    "score": round(self.eligibility_score, 3),
                    "weight": self.eligibility_weight,
                },
                "time": {
                    "score": round(self.time_score, 3),
                    "weight": self.time_weight,
                },
                "team": {
                    "score": round(self.team_score, 3),
                    "weight": self.team_weight,
                },
                "intent": {
                    "score": round(self.intent_score, 3),
                    "weight": self.intent_weight,
                },
            },
        }


@dataclass
class MatchResult:
    """Result of matching a profile to an opportunity."""

    opportunity_id: str
    batch_id: str
    score: float
    breakdown: ScoreBreakdown
    eligible: bool
    reasons: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    match_reasons: List[str] = field(default_factory=list)  # Why it's a good match


class MatchingScorer:
    """Multi-factor scoring engine for matching."""

    # Intent to opportunity category mapping
    INTENT_CATEGORY_MAP = {
        "funding": ["grant", "accelerator", "competition"],
        "exposure": ["hackathon", "competition", "accelerator"],
        "learning": ["hackathon", "competition"],
        "networking": ["hackathon", "accelerator", "conference"],
        "prizes": ["hackathon", "competition", "bug-bounty"],
        "equity": ["accelerator"],
        "mentorship": ["accelerator"],
    }

    def __init__(self):
        self.dsl_engine = DSLEngine()

    def calculate_match(
        self,
        profile_context: ProfileContext,
        opportunity_context: OpportunityContext,
        opportunity_id: str,
        batch_id: str,
        profile_embedding: Optional[List[float]] = None,
        opportunity_embedding: Optional[List[float]] = None,
        deadline: Optional[datetime] = None,
        event_start: Optional[datetime] = None,
        event_end: Optional[datetime] = None,
        opportunity_category: Optional[str] = None,
        profile_intents: Optional[List[str]] = None,
        rules_dsl: Optional[Dict] = None,
    ) -> MatchResult:
        """
        Calculate match score between a profile and opportunity.

        Args:
            profile_context: Profile context for eligibility
            opportunity_context: Opportunity context for eligibility
            opportunity_id: ID of the opportunity
            batch_id: ID of the batch
            profile_embedding: Profile embedding vector
            opportunity_embedding: Opportunity embedding vector
            deadline: Submission deadline
            event_start: Event start time
            event_end: Event end time
            opportunity_category: Category (hackathon, grant, etc.)
            profile_intents: User's goals
            rules_dsl: Optional custom eligibility rules

        Returns:
            MatchResult with score breakdown
        """
        breakdown = ScoreBreakdown()
        match_reasons = []
        suggestions = []

        # 1. Semantic similarity score
        if profile_embedding and opportunity_embedding:
            breakdown.semantic_score = self._cosine_similarity(
                profile_embedding, opportunity_embedding
            )
            if breakdown.semantic_score > 0.7:
                match_reasons.append("Strong skill/interest alignment")
            elif breakdown.semantic_score > 0.5:
                match_reasons.append("Good skill/interest match")
        else:
            breakdown.semantic_score = 0.5  # Neutral if no embeddings

        # 2. Eligibility score
        eligibility_result = self.dsl_engine.evaluate(
            profile_context, opportunity_context, rules_dsl
        )
        breakdown.eligibility_score = eligibility_result.score
        suggestions.extend(eligibility_result.suggestions)

        if eligibility_result.eligible:
            match_reasons.append("Meets all eligibility requirements")

        # 3. Time fit score
        breakdown.time_score = self._calculate_time_score(
            deadline, event_start, event_end
        )
        if breakdown.time_score > 0.8:
            match_reasons.append("Great timing - deadline approaching")
        elif breakdown.time_score > 0.6:
            match_reasons.append("Good timeline fit")

        # 4. Team fit score
        breakdown.team_score = self._calculate_team_score(
            profile_context.team_size,
            opportunity_context.team_min,
            opportunity_context.team_max,
        )
        if breakdown.team_score == 1.0:
            match_reasons.append("Perfect team size match")

        # 5. Intent alignment score
        breakdown.intent_score = self._calculate_intent_score(
            profile_intents or [], opportunity_category
        )
        if breakdown.intent_score > 0.8:
            match_reasons.append("Aligns with your goals")

        return MatchResult(
            opportunity_id=opportunity_id,
            batch_id=batch_id,
            score=breakdown.total_score,
            breakdown=breakdown,
            eligible=eligibility_result.eligible,
            reasons=eligibility_result.reasons,
            suggestions=suggestions,
            match_reasons=match_reasons,
        )

    def _cosine_similarity(
        self, vec1: List[float], vec2: List[float]
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
            # Normalize to 0-1 range (cosine similarity is -1 to 1)
            return (similarity + 1) / 2
        except Exception as e:
            logger.warning(f"Error calculating cosine similarity: {e}")
            return 0.5

    def _calculate_time_score(
        self,
        deadline: Optional[datetime],
        event_start: Optional[datetime],
        event_end: Optional[datetime],
    ) -> float:
        """
        Calculate time fit score.

        - Higher score for opportunities with deadlines 1-4 weeks away
        - Lower score for very close deadlines (< 3 days) or very far (> 3 months)
        """
        if not deadline:
            return 0.7  # Neutral for no deadline

        now = datetime.now()
        days_until_deadline = (deadline - now).days

        if days_until_deadline < 0:
            return 0.0  # Past deadline

        if days_until_deadline <= 3:
            return 0.3  # Very soon, might be rushed

        if days_until_deadline <= 7:
            return 0.7  # One week - good urgency

        if days_until_deadline <= 14:
            return 1.0  # Sweet spot: 1-2 weeks

        if days_until_deadline <= 30:
            return 0.9  # Good - about a month

        if days_until_deadline <= 60:
            return 0.7  # Okay - 1-2 months

        if days_until_deadline <= 90:
            return 0.5  # Far out - 2-3 months

        return 0.3  # Very far out

    def _calculate_team_score(
        self,
        team_size: int,
        team_min: Optional[int],
        team_max: Optional[int],
    ) -> float:
        """Calculate team size fit score."""
        if team_min is None and team_max is None:
            return 1.0  # No restrictions

        if team_min and team_size < team_min:
            # Below minimum - score based on how close
            return max(0.0, 1.0 - (team_min - team_size) * 0.3)

        if team_max and team_size > team_max:
            # Above maximum - score based on how far
            return max(0.0, 1.0 - (team_size - team_max) * 0.3)

        # Within range
        return 1.0

    def _calculate_intent_score(
        self,
        intents: List[str],
        category: Optional[str],
    ) -> float:
        """Calculate how well opportunity category matches user intents."""
        if not intents or not category:
            return 0.5  # Neutral

        category_lower = category.lower()
        total_match = 0.0

        for intent in intents:
            intent_lower = intent.lower()
            matching_categories = self.INTENT_CATEGORY_MAP.get(intent_lower, [])

            if category_lower in matching_categories:
                total_match += 1.0
            elif any(cat in category_lower for cat in matching_categories):
                total_match += 0.5

        if not intents:
            return 0.5

        return min(1.0, total_match / len(intents))


# Singleton instance
_scorer: Optional[MatchingScorer] = None


def get_scorer() -> MatchingScorer:
    """Get or create the scorer singleton."""
    global _scorer
    if _scorer is None:
        _scorer = MatchingScorer()
    return _scorer
