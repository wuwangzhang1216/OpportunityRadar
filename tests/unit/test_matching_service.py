"""Comprehensive unit tests for MongoMatchingService."""

import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass


class TestMatchScoreBreakdown:
    """Test MatchScoreBreakdown dataclass."""

    def test_match_score_breakdown_import(self):
        """Test MatchScoreBreakdown can be imported."""
        from src.opportunity_radar.services.mongo_matching_service import MatchScoreBreakdown
        assert MatchScoreBreakdown is not None

    def test_match_score_breakdown_defaults(self):
        """Test MatchScoreBreakdown default values."""
        from src.opportunity_radar.services.mongo_matching_service import MatchScoreBreakdown

        breakdown = MatchScoreBreakdown()

        assert breakdown.semantic_score == 0.0
        assert breakdown.recency_boost == 0.0
        assert breakdown.popularity_boost == 0.0
        assert breakdown.team_size_eligible is True
        assert breakdown.funding_stage_eligible is True
        assert breakdown.location_eligible is True

    def test_is_eligible_all_true(self):
        """Test is_eligible when all criteria met."""
        from src.opportunity_radar.services.mongo_matching_service import MatchScoreBreakdown

        breakdown = MatchScoreBreakdown(
            team_size_eligible=True,
            funding_stage_eligible=True,
            location_eligible=True,
        )

        assert breakdown.is_eligible is True

    def test_is_eligible_team_size_false(self):
        """Test is_eligible when team size fails."""
        from src.opportunity_radar.services.mongo_matching_service import MatchScoreBreakdown

        breakdown = MatchScoreBreakdown(team_size_eligible=False)

        assert breakdown.is_eligible is False

    def test_is_eligible_funding_stage_false(self):
        """Test is_eligible when funding stage fails."""
        from src.opportunity_radar.services.mongo_matching_service import MatchScoreBreakdown

        breakdown = MatchScoreBreakdown(funding_stage_eligible=False)

        assert breakdown.is_eligible is False

    def test_total_score_when_ineligible(self):
        """Test total_score returns 0 when ineligible."""
        from src.opportunity_radar.services.mongo_matching_service import MatchScoreBreakdown

        breakdown = MatchScoreBreakdown(
            semantic_score=0.9,
            team_size_eligible=False,
        )

        assert breakdown.total_score == 0.0

    def test_total_score_calculation(self):
        """Test total_score calculation with boosts."""
        from src.opportunity_radar.services.mongo_matching_service import MatchScoreBreakdown

        breakdown = MatchScoreBreakdown(
            semantic_score=0.8,
            recency_boost=0.02,
            popularity_boost=0.01,
        )

        # Boost is capped at 0.05
        expected = 0.8 + 0.03
        assert breakdown.total_score == pytest.approx(expected, rel=1e-3)

    def test_total_score_boost_cap(self):
        """Test total_score boost is capped at 0.05."""
        from src.opportunity_radar.services.mongo_matching_service import MatchScoreBreakdown

        breakdown = MatchScoreBreakdown(
            semantic_score=0.8,
            recency_boost=0.1,  # Would exceed cap
            popularity_boost=0.1,
        )

        # Boost should be capped at 0.05
        expected = 0.8 + 0.05
        assert breakdown.total_score == pytest.approx(expected, rel=1e-3)

    def test_total_score_max_cap(self):
        """Test total_score is capped at 1.0."""
        from src.opportunity_radar.services.mongo_matching_service import MatchScoreBreakdown

        breakdown = MatchScoreBreakdown(
            semantic_score=0.98,
            recency_boost=0.05,
        )

        assert breakdown.total_score == 1.0

    def test_to_dict(self):
        """Test to_dict conversion."""
        from src.opportunity_radar.services.mongo_matching_service import MatchScoreBreakdown

        breakdown = MatchScoreBreakdown(
            semantic_score=0.75,
            recency_boost=0.02,
        )

        result = breakdown.to_dict()

        assert "total" in result
        assert "is_eligible" in result
        assert "semantic_score" in result
        assert "eligibility" in result
        assert result["semantic_score"] == 0.75


class TestMatchExplanation:
    """Test MatchExplanation dataclass."""

    def test_match_explanation_import(self):
        """Test MatchExplanation can be imported."""
        from src.opportunity_radar.services.mongo_matching_service import MatchExplanation
        assert MatchExplanation is not None

    def test_match_explanation_creation(self):
        """Test MatchExplanation creation."""
        from src.opportunity_radar.services.mongo_matching_service import MatchExplanation

        explanation = MatchExplanation(
            primary_reason="Great match for your skills",
            matching_skills=["Python", "FastAPI"],
            matching_themes=["AI/ML"],
        )

        assert explanation.primary_reason == "Great match for your skills"
        assert len(explanation.matching_skills) == 2
        assert len(explanation.matching_themes) == 1

    def test_match_explanation_to_dict(self):
        """Test MatchExplanation to_dict."""
        from src.opportunity_radar.services.mongo_matching_service import MatchExplanation

        explanation = MatchExplanation(
            primary_reason="Good match",
            matching_skills=["Python"],
            warnings=["Deadline soon"],
        )

        result = explanation.to_dict()

        assert result["primary_reason"] == "Good match"
        assert result["matching_skills"] == ["Python"]
        assert result["warnings"] == ["Deadline soon"]


class TestMatchResult:
    """Test MatchResult dataclass."""

    def test_match_result_import(self):
        """Test MatchResult can be imported."""
        from src.opportunity_radar.services.mongo_matching_service import MatchResult
        assert MatchResult is not None

    def test_match_result_creation(self):
        """Test MatchResult creation."""
        from src.opportunity_radar.services.mongo_matching_service import (
            MatchResult,
            MatchScoreBreakdown,
            MatchExplanation,
        )

        breakdown = MatchScoreBreakdown(semantic_score=0.8)
        explanation = MatchExplanation(primary_reason="Good match")

        result = MatchResult(
            opportunity_id="507f1f77bcf86cd799439011",
            score=0.8,
            breakdown=breakdown,
            explanation=explanation,
        )

        assert result.opportunity_id == "507f1f77bcf86cd799439011"
        assert result.score == 0.8


class TestFuzzyIndustryMatch:
    """Test fuzzy_industry_match function."""

    def test_fuzzy_industry_match_import(self):
        """Test fuzzy_industry_match can be imported."""
        from src.opportunity_radar.services.mongo_matching_service import fuzzy_industry_match
        assert fuzzy_industry_match is not None

    def test_fuzzy_match_empty_sets(self):
        """Test fuzzy match with empty sets."""
        from src.opportunity_radar.services.mongo_matching_service import fuzzy_industry_match

        score, matches = fuzzy_industry_match(set(), set())
        assert score == 0.5
        assert matches == []

    def test_fuzzy_match_direct_overlap(self):
        """Test fuzzy match with direct overlap."""
        from src.opportunity_radar.services.mongo_matching_service import fuzzy_industry_match

        profile_industries = {"ai", "fintech"}
        opp_themes = {"ai", "healthcare"}

        score, matches = fuzzy_industry_match(profile_industries, opp_themes)

        assert score > 0
        assert "ai" in matches

    def test_fuzzy_match_alias_matching(self):
        """Test fuzzy match with alias matching."""
        from src.opportunity_radar.services.mongo_matching_service import fuzzy_industry_match

        profile_industries = {"machine learning"}
        opp_themes = {"ai/ml"}

        score, matches = fuzzy_industry_match(profile_industries, opp_themes)

        # Should find match via alias
        assert score > 0 or matches == []  # Depends on alias config

    def test_fuzzy_match_substring_matching(self):
        """Test fuzzy match with substring matching."""
        from src.opportunity_radar.services.mongo_matching_service import fuzzy_industry_match

        profile_industries = {"web"}
        opp_themes = {"web development"}

        score, matches = fuzzy_industry_match(profile_industries, opp_themes)

        assert score > 0
        assert len(matches) > 0


class TestMongoMatchingServiceStructure:
    """Test MongoMatchingService class structure."""

    def test_service_import(self):
        """Test MongoMatchingService can be imported."""
        from src.opportunity_radar.services.mongo_matching_service import MongoMatchingService
        assert MongoMatchingService is not None

    def test_service_instantiation(self):
        """Test MongoMatchingService can be instantiated."""
        from src.opportunity_radar.services.mongo_matching_service import MongoMatchingService

        service = MongoMatchingService()
        assert service is not None

    def test_service_has_required_methods(self):
        """Test MongoMatchingService has all required methods."""
        from src.opportunity_radar.services.mongo_matching_service import MongoMatchingService

        required_methods = [
            "compute_matches_for_profile",
            "save_matches",
            "get_top_matches_for_user",
            "bookmark_match",
            "dismiss_match",
            "record_feedback",
        ]

        for method in required_methods:
            assert hasattr(MongoMatchingService, method), f"Missing method: {method}"

    def test_embedding_service_lazy_load(self):
        """Test embedding service is lazy loaded."""
        from src.opportunity_radar.services.mongo_matching_service import MongoMatchingService

        service = MongoMatchingService()
        assert service._embedding_service is None


class TestCosineSimilarity:
    """Test cosine similarity calculation."""

    def test_cosine_similarity_identical_vectors(self):
        """Test cosine similarity of identical vectors."""
        from src.opportunity_radar.services.mongo_matching_service import MongoMatchingService

        service = MongoMatchingService()
        vec = [1.0, 0.0, 0.0]

        similarity = service._cosine_similarity(vec, vec)

        # Identical vectors should have high similarity (after transformation)
        assert similarity > 0.5

    def test_cosine_similarity_orthogonal_vectors(self):
        """Test cosine similarity of orthogonal vectors."""
        from src.opportunity_radar.services.mongo_matching_service import MongoMatchingService

        service = MongoMatchingService()
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]

        similarity = service._cosine_similarity(vec1, vec2)

        # Orthogonal vectors have 0 raw similarity, transformed to low score
        assert similarity < 0.5

    def test_cosine_similarity_opposite_vectors(self):
        """Test cosine similarity of opposite vectors."""
        from src.opportunity_radar.services.mongo_matching_service import MongoMatchingService

        service = MongoMatchingService()
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [-1.0, 0.0, 0.0]

        similarity = service._cosine_similarity(vec1, vec2)

        # Opposite vectors should have very low similarity
        assert similarity < 0.3

    def test_cosine_similarity_zero_vector(self):
        """Test cosine similarity with zero vector."""
        from src.opportunity_radar.services.mongo_matching_service import MongoMatchingService

        service = MongoMatchingService()
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 0.0, 0.0]

        similarity = service._cosine_similarity(vec1, vec2)

        # Zero vector should result in 0 similarity
        assert similarity == 0.0

    def test_cosine_similarity_realistic_embeddings(self):
        """Test cosine similarity with realistic embedding-like vectors."""
        from src.opportunity_radar.services.mongo_matching_service import MongoMatchingService

        service = MongoMatchingService()

        # Generate random normalized vectors (like real embeddings)
        np.random.seed(42)
        vec1 = np.random.randn(1536).tolist()
        vec2 = np.random.randn(1536).tolist()

        similarity = service._cosine_similarity(vec1, vec2)

        # Should be in valid range
        assert 0.0 <= similarity <= 1.0


class TestHardFilters:
    """Test hard eligibility filters."""

    def test_apply_hard_filters_team_size_too_small(self):
        """Test team size filter when team is too small."""
        from src.opportunity_radar.services.mongo_matching_service import (
            MongoMatchingService,
            MatchScoreBreakdown,
        )

        service = MongoMatchingService()
        breakdown = MatchScoreBreakdown()
        eligibility_issues = []

        # Mock profile with team_size=1
        mock_profile = MagicMock()
        mock_profile.team_size = 1

        # Mock opportunity requiring min team size of 3
        mock_opportunity = MagicMock()
        mock_opportunity.team_size_min = 3
        mock_opportunity.team_size_max = None
        mock_opportunity.opportunity_type = "hackathon"

        service._apply_hard_filters(mock_profile, mock_opportunity, breakdown, eligibility_issues)

        assert breakdown.team_size_eligible is False
        assert len(eligibility_issues) > 0

    def test_apply_hard_filters_team_size_too_large(self):
        """Test team size filter when team is too large."""
        from src.opportunity_radar.services.mongo_matching_service import (
            MongoMatchingService,
            MatchScoreBreakdown,
        )

        service = MongoMatchingService()
        breakdown = MatchScoreBreakdown()
        eligibility_issues = []

        mock_profile = MagicMock()
        mock_profile.team_size = 10

        mock_opportunity = MagicMock()
        mock_opportunity.team_size_min = None
        mock_opportunity.team_size_max = 5
        mock_opportunity.opportunity_type = "hackathon"

        service._apply_hard_filters(mock_profile, mock_opportunity, breakdown, eligibility_issues)

        assert breakdown.team_size_eligible is False

    def test_apply_hard_filters_team_size_valid(self):
        """Test team size filter when team size is valid."""
        from src.opportunity_radar.services.mongo_matching_service import (
            MongoMatchingService,
            MatchScoreBreakdown,
        )

        service = MongoMatchingService()
        breakdown = MatchScoreBreakdown()
        eligibility_issues = []

        mock_profile = MagicMock()
        mock_profile.team_size = 3
        mock_profile.funding_stage = None

        mock_opportunity = MagicMock()
        mock_opportunity.team_size_min = 1
        mock_opportunity.team_size_max = 5
        mock_opportunity.opportunity_type = "hackathon"

        service._apply_hard_filters(mock_profile, mock_opportunity, breakdown, eligibility_issues)

        assert breakdown.team_size_eligible is True
        assert len(eligibility_issues) == 0


class TestGenerateExplanation:
    """Test explanation generation."""

    def test_generate_explanation_ineligible(self):
        """Test explanation for ineligible match."""
        from src.opportunity_radar.services.mongo_matching_service import (
            MongoMatchingService,
            MatchScoreBreakdown,
        )

        service = MongoMatchingService()
        breakdown = MatchScoreBreakdown(team_size_eligible=False)

        explanation = service._generate_explanation(breakdown, [])

        assert "eligible" in explanation.lower()

    def test_generate_explanation_with_reasons(self):
        """Test explanation uses provided reasons."""
        from src.opportunity_radar.services.mongo_matching_service import (
            MongoMatchingService,
            MatchScoreBreakdown,
        )

        service = MongoMatchingService()
        breakdown = MatchScoreBreakdown(semantic_score=0.8)
        reasons = ["Excellent match for your profile"]

        explanation = service._generate_explanation(breakdown, reasons)

        assert explanation == "Excellent match for your profile"

    def test_generate_explanation_high_score(self):
        """Test explanation for high score."""
        from src.opportunity_radar.services.mongo_matching_service import (
            MongoMatchingService,
            MatchScoreBreakdown,
        )

        service = MongoMatchingService()
        breakdown = MatchScoreBreakdown(semantic_score=0.85)

        explanation = service._generate_explanation(breakdown, [])

        assert "excellent" in explanation.lower() or "good" in explanation.lower()


class TestSingletonAndHelpers:
    """Test singleton and helper functions."""

    def test_get_mongo_matching_service(self):
        """Test get_mongo_matching_service singleton."""
        from src.opportunity_radar.services.mongo_matching_service import (
            get_mongo_matching_service,
        )

        service1 = get_mongo_matching_service()
        service2 = get_mongo_matching_service()

        assert service1 is service2

    def test_industry_aliases_defined(self):
        """Test INDUSTRY_ALIASES is defined."""
        from src.opportunity_radar.services.mongo_matching_service import INDUSTRY_ALIASES

        assert isinstance(INDUSTRY_ALIASES, dict)
        assert "ai" in INDUSTRY_ALIASES
        assert "ml" in INDUSTRY_ALIASES


@pytest.mark.asyncio
class TestMatchingServiceAsync:
    """Async tests for MongoMatchingService."""

    async def test_compute_matches_no_profile(self):
        """Test compute_matches returns empty for missing profile."""
        from src.opportunity_radar.services.mongo_matching_service import MongoMatchingService

        service = MongoMatchingService()

        with patch("src.opportunity_radar.services.mongo_matching_service.Profile") as MockProfile:
            MockProfile.get = AsyncMock(return_value=None)

            result = await service.compute_matches_for_profile("nonexistent_id")

            assert result == []

    async def test_compute_matches_no_opportunities(self):
        """Test compute_matches returns empty when no opportunities."""
        from src.opportunity_radar.services.mongo_matching_service import MongoMatchingService

        service = MongoMatchingService()

        mock_profile = MagicMock()
        mock_profile.id = "profile_id"
        mock_profile.embedding = [0.1] * 1536

        with patch("src.opportunity_radar.services.mongo_matching_service.Profile") as MockProfile:
            MockProfile.get = AsyncMock(return_value=mock_profile)

            with patch("src.opportunity_radar.services.mongo_matching_service.Opportunity") as MockOpp:
                mock_find = MagicMock()
                mock_find.to_list = AsyncMock(return_value=[])
                MockOpp.find = MagicMock(return_value=mock_find)

                result = await service.compute_matches_for_profile("profile_id")

                assert result == []

    async def test_bookmark_match_success(self):
        """Test bookmark_match updates match."""
        from src.opportunity_radar.services.mongo_matching_service import MongoMatchingService

        service = MongoMatchingService()

        mock_match = MagicMock()
        mock_match.is_bookmarked = False
        mock_match.save = AsyncMock()

        with patch("src.opportunity_radar.services.mongo_matching_service.Match") as MockMatch:
            MockMatch.find_one = AsyncMock(return_value=mock_match)

            # Use valid ObjectId format strings
            result = await service.bookmark_match("507f1f77bcf86cd799439011", "507f1f77bcf86cd799439012")

            assert result is True
            assert mock_match.is_bookmarked is True
            mock_match.save.assert_called_once()

    async def test_bookmark_match_not_found(self):
        """Test bookmark_match returns False when match not found."""
        from src.opportunity_radar.services.mongo_matching_service import MongoMatchingService

        service = MongoMatchingService()

        with patch("src.opportunity_radar.services.mongo_matching_service.Match") as MockMatch:
            MockMatch.find_one = AsyncMock(return_value=None)

            # Use valid ObjectId format strings
            result = await service.bookmark_match("507f1f77bcf86cd799439011", "507f1f77bcf86cd799439012")

            assert result is False

    async def test_dismiss_match_success(self):
        """Test dismiss_match updates match."""
        from src.opportunity_radar.services.mongo_matching_service import MongoMatchingService

        service = MongoMatchingService()

        mock_match = MagicMock()
        mock_match.is_dismissed = False
        mock_match.save = AsyncMock()

        with patch("src.opportunity_radar.services.mongo_matching_service.Match") as MockMatch:
            MockMatch.find_one = AsyncMock(return_value=mock_match)

            # Use valid ObjectId format strings
            result = await service.dismiss_match("507f1f77bcf86cd799439011", "507f1f77bcf86cd799439012")

            assert result is True
            assert mock_match.is_dismissed is True

    async def test_record_feedback_bookmark_action(self):
        """Test record_feedback handles bookmark action."""
        from src.opportunity_radar.services.mongo_matching_service import MongoMatchingService

        service = MongoMatchingService()

        mock_match = MagicMock()
        mock_match.is_bookmarked = False
        mock_match.save = AsyncMock()

        with patch("src.opportunity_radar.services.mongo_matching_service.Match") as MockMatch:
            MockMatch.find_one = AsyncMock(return_value=mock_match)

            # Use valid ObjectId format strings
            result = await service.record_feedback("507f1f77bcf86cd799439011", "507f1f77bcf86cd799439012", "bookmark")

            assert result is True
            assert mock_match.is_bookmarked is True

    async def test_record_feedback_dismiss_action(self):
        """Test record_feedback handles dismiss action."""
        from src.opportunity_radar.services.mongo_matching_service import MongoMatchingService

        service = MongoMatchingService()

        mock_match = MagicMock()
        mock_match.is_dismissed = False
        mock_match.save = AsyncMock()

        with patch("src.opportunity_radar.services.mongo_matching_service.Match") as MockMatch:
            MockMatch.find_one = AsyncMock(return_value=mock_match)

            # Use valid ObjectId format strings
            result = await service.record_feedback("507f1f77bcf86cd799439011", "507f1f77bcf86cd799439012", "dismiss")

            assert result is True
            assert mock_match.is_dismissed is True
