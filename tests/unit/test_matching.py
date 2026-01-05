"""Unit tests for matching engine."""

import pytest


class TestDSLEngine:
    """Test DSL Engine functionality."""

    def test_import_dsl_engine(self):
        """Test DSLEngine import."""
        from src.opportunity_radar.matching import DSLEngine

        assert DSLEngine is not None

    def test_dsl_engine_initialization(self):
        """Test DSLEngine can be initialized."""
        from src.opportunity_radar.matching.dsl_engine import DSLEngine

        engine = DSLEngine()
        assert engine is not None

    def test_eligible_profile_evaluation(self):
        """Test evaluation of eligible profile."""
        from src.opportunity_radar.matching.dsl_engine import (
            DSLEngine,
            OpportunityContext,
            ProfileContext,
        )

        engine = DSLEngine()

        profile = ProfileContext(
            profile_type="developer",
            tech_stack=["Python", "React"],
            industries=["FinTech"],
            region="US",
            team_size=2,
            is_student=False,
        )

        opp = OpportunityContext(
            regions=["US", "Global"],
            team_min=1,
            team_max=5,
            student_only=False,
            required_tech=["Python"],
        )

        result = engine.evaluate(profile, opp)

        assert result.eligible is True
        assert result.score >= 0.5

    def test_student_only_rejection(self):
        """Test non-student rejected from student-only opportunity."""
        from src.opportunity_radar.matching.dsl_engine import (
            DSLEngine,
            OpportunityContext,
            ProfileContext,
        )

        engine = DSLEngine()

        profile = ProfileContext(
            profile_type="developer",
            tech_stack=["Python"],
            region="US",
            is_student=False,
        )

        opp = OpportunityContext(
            regions=["US"],
            student_only=True,
        )

        result = engine.evaluate(profile, opp)

        assert result.eligible is False

    def test_region_mismatch(self):
        """Test region mismatch detection."""
        from src.opportunity_radar.matching.dsl_engine import (
            DSLEngine,
            OpportunityContext,
            ProfileContext,
        )

        engine = DSLEngine()

        profile = ProfileContext(
            profile_type="developer",
            tech_stack=["Python"],
            region="Germany",
        )

        opp = OpportunityContext(
            regions=["US"],
            remote_ok=False,
        )

        result = engine.evaluate(profile, opp)

        assert result.eligible is False


class TestMatchingScorer:
    """Test Matching Scorer functionality."""

    def test_import_matching_scorer(self):
        """Test MatchingScorer import."""
        from src.opportunity_radar.matching import MatchingScorer

        assert MatchingScorer is not None

    def test_scorer_initialization(self):
        """Test MatchingScorer initialization with DSL Engine."""
        from src.opportunity_radar.matching.scorer import MatchingScorer

        scorer = MatchingScorer()
        assert scorer.dsl_engine is not None

    def test_score_breakdown_calculation(self):
        """Test ScoreBreakdown computation."""
        from src.opportunity_radar.matching.scorer import ScoreBreakdown

        breakdown = ScoreBreakdown(
            semantic_score=0.8,
            eligibility_score=1.0,
            time_score=0.7,
            team_score=0.9,
            intent_score=0.6,
        )

        assert breakdown.total_score > 0
        assert 0 <= breakdown.total_score <= 1

    def test_score_breakdown_all_zeros(self):
        """Test ScoreBreakdown with all zeros."""
        from src.opportunity_radar.matching.scorer import ScoreBreakdown

        breakdown = ScoreBreakdown(
            semantic_score=0.0,
            eligibility_score=0.0,
            time_score=0.0,
            team_score=0.0,
            intent_score=0.0,
        )

        assert breakdown.total_score == 0.0

    def test_score_breakdown_all_ones(self):
        """Test ScoreBreakdown with all ones."""
        from src.opportunity_radar.matching.scorer import ScoreBreakdown

        breakdown = ScoreBreakdown(
            semantic_score=1.0,
            eligibility_score=1.0,
            time_score=1.0,
            team_score=1.0,
            intent_score=1.0,
        )

        assert breakdown.total_score == 1.0
