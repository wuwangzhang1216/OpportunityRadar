#!/usr/bin/env python3
"""System integration test script for OpportunityRadar."""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def test_imports():
    """Test all critical imports."""
    print("=" * 60)
    print("Testing Imports...")
    print("=" * 60)

    tests = []

    # Core
    try:
        from src.opportunity_radar.config import settings
        tests.append(("Config", True, None))
    except Exception as e:
        tests.append(("Config", False, str(e)))

    try:
        from src.opportunity_radar.core.security import get_current_user, create_access_token
        tests.append(("Security", True, None))
    except Exception as e:
        tests.append(("Security", False, str(e)))

    # Models
    try:
        from src.opportunity_radar.models import User, Profile, Opportunity, Batch, Match, Pipeline, Material
        tests.append(("Models", True, None))
    except Exception as e:
        tests.append(("Models", False, str(e)))

    # Services
    try:
        from src.opportunity_radar.services import (
            AuthService, OpportunityService, EmbeddingService,
            MatchingService, ProfileService, MaterialService, PipelineService
        )
        tests.append(("Services", True, None))
    except Exception as e:
        tests.append(("Services", False, str(e)))

    # Matching
    try:
        from src.opportunity_radar.matching import DSLEngine, MatchingScorer
        tests.append(("Matching Engine", True, None))
    except Exception as e:
        tests.append(("Matching Engine", False, str(e)))

    # AI
    try:
        from src.opportunity_radar.ai import MaterialGenerator, OpenAIClient
        tests.append(("AI Module", True, None))
    except Exception as e:
        tests.append(("AI Module", False, str(e)))

    # Scrapers
    try:
        from src.opportunity_radar.scrapers import (
            DevpostScraper, MLHScraper, ETHGlobalScraper, KaggleScraper,
            HackerEarthScraper, GrantsGovScraper, SBIRScraper
        )
        tests.append(("Scrapers", True, None))
    except Exception as e:
        tests.append(("Scrapers", False, str(e)))

    # API
    try:
        from src.opportunity_radar.api.v1.router import api_router
        tests.append(("API Router", True, None))
    except Exception as e:
        tests.append(("API Router", False, str(e)))

    # FastAPI App
    try:
        from src.opportunity_radar.main import app
        tests.append(("FastAPI App", True, None))
    except Exception as e:
        tests.append(("FastAPI App", False, str(e)))

    # Print results
    passed = 0
    failed = 0
    for name, success, error in tests:
        if success:
            print(f"  ✓ {name}")
            passed += 1
        else:
            print(f"  ✗ {name}: {error}")
            failed += 1

    print()
    print(f"Import Tests: {passed} passed, {failed} failed")
    return failed == 0


def test_dsl_engine():
    """Test DSL Engine functionality."""
    print()
    print("=" * 60)
    print("Testing DSL Engine...")
    print("=" * 60)

    from src.opportunity_radar.matching.dsl_engine import DSLEngine, ProfileContext, OpportunityContext

    engine = DSLEngine()

    # Test 1: Eligible profile
    profile = ProfileContext(
        profile_type='developer',
        tech_stack=['Python', 'React'],
        industries=['FinTech'],
        region='US',
        team_size=2,
        is_student=False
    )

    opp = OpportunityContext(
        regions=['US', 'Global'],
        team_min=1,
        team_max=5,
        student_only=False,
        required_tech=['Python']
    )

    result = engine.evaluate(profile, opp)

    if result.eligible and result.score >= 0.5:
        print("  ✓ Eligible profile correctly identified")
    else:
        print(f"  ✗ Eligible profile test failed: eligible={result.eligible}, score={result.score}")
        return False

    # Test 2: Ineligible profile (student only)
    opp_student = OpportunityContext(
        regions=['US'],
        student_only=True
    )

    result2 = engine.evaluate(profile, opp_student)

    if not result2.eligible:
        print("  ✓ Non-student correctly rejected from student-only")
    else:
        print("  ✗ Non-student should be rejected from student-only")
        return False

    # Test 3: Region mismatch
    profile_eu = ProfileContext(
        profile_type='developer',
        tech_stack=['Python'],
        region='Germany'
    )

    opp_us_only = OpportunityContext(
        regions=['US'],
        remote_ok=False
    )

    result3 = engine.evaluate(profile_eu, opp_us_only)

    if not result3.eligible:
        print("  ✓ Region mismatch correctly detected")
    else:
        print("  ✗ Region mismatch should fail")
        return False

    print()
    print("DSL Engine Tests: All passed")
    return True


def test_scorer():
    """Test Matching Scorer."""
    print()
    print("=" * 60)
    print("Testing Matching Scorer...")
    print("=" * 60)

    from src.opportunity_radar.matching.scorer import MatchingScorer, ScoreBreakdown

    scorer = MatchingScorer()

    # Test initialization
    if scorer.dsl_engine is not None:
        print("  ✓ Scorer initialized with DSL Engine")
    else:
        print("  ✗ Scorer missing DSL Engine")
        return False

    # Test ScoreBreakdown
    breakdown = ScoreBreakdown(
        semantic_score=0.8,
        eligibility_score=1.0,
        time_score=0.7,
        team_score=0.9,
        intent_score=0.6
    )

    if breakdown.total_score > 0:
        print(f"  ✓ ScoreBreakdown computed: {breakdown.total_score:.2f}")
    else:
        print("  ✗ ScoreBreakdown computation failed")
        return False

    print()
    print("Scorer Tests: All passed")
    return True


def test_ai_prompts():
    """Test AI prompt generation."""
    print()
    print("=" * 60)
    print("Testing AI Prompts...")
    print("=" * 60)

    from src.opportunity_radar.ai.prompts.templates import (
        build_readme_prompt, build_pitch_prompt, build_demo_script_prompt, build_qa_prompt
    )

    # Test README prompt
    readme = build_readme_prompt(
        project_name="TestApp",
        problem="Users can't do X",
        solution="Our app does Y",
        tech_stack=["Python", "FastAPI"],
        opportunity_title="Hackathon 2024",
        opportunity_themes=["AI", "Cloud"]
    )

    if len(readme) > 100 and "TestApp" in readme:
        print(f"  ✓ README prompt generated ({len(readme)} chars)")
    else:
        print("  ✗ README prompt generation failed")
        return False

    # Test Pitch prompt
    pitch = build_pitch_prompt(
        project_name="TestApp",
        problem="Users can't do X",
        solution="Our app does Y",
        tech_stack=["Python"],
        opportunity_title="Hackathon 2024",
        time_limit_min=3
    )

    if len(pitch) > 100 and "3" in pitch:
        print(f"  ✓ Pitch prompt generated ({len(pitch)} chars)")
    else:
        print("  ✗ Pitch prompt generation failed")
        return False

    # Test Demo Script prompt
    demo = build_demo_script_prompt(
        project_name="TestApp",
        solution="Our app does Y",
        tech_stack=["Python"],
        features=["Feature A", "Feature B"],
        time_limit_min=2
    )

    if len(demo) > 100:
        print(f"  ✓ Demo script prompt generated ({len(demo)} chars)")
    else:
        print("  ✗ Demo script prompt generation failed")
        return False

    # Test Q&A prompt
    qa = build_qa_prompt(
        project_name="TestApp",
        problem="Users can't do X",
        solution="Our app does Y",
        tech_stack=["Python"],
        opportunity_title="Hackathon 2024",
        opportunity_themes=["AI"]
    )

    if len(qa) > 100:
        print(f"  ✓ Q&A prompt generated ({len(qa)} chars)")
    else:
        print("  ✗ Q&A prompt generation failed")
        return False

    print()
    print("AI Prompt Tests: All passed")
    return True


def test_scrapers():
    """Test scraper initialization."""
    print()
    print("=" * 60)
    print("Testing Scrapers...")
    print("=" * 60)

    from src.opportunity_radar.scrapers import (
        DevpostScraper, MLHScraper, ETHGlobalScraper, KaggleScraper,
        HackerEarthScraper, GrantsGovScraper, SBIRScraper, EUHorizonScraper,
        InnovateUKScraper, HackerOneScraper, YCombinatorScraper, OpenSourceGrantsScraper
    )

    scrapers = [
        DevpostScraper, MLHScraper, ETHGlobalScraper, KaggleScraper,
        HackerEarthScraper, GrantsGovScraper, SBIRScraper, EUHorizonScraper,
        InnovateUKScraper, HackerOneScraper, YCombinatorScraper, OpenSourceGrantsScraper
    ]

    for scraper_cls in scrapers:
        try:
            s = scraper_cls()
            print(f"  ✓ {s.source_name}")
        except Exception as e:
            print(f"  ✗ {scraper_cls.__name__}: {e}")
            return False

    print()
    print(f"Scraper Tests: All {len(scrapers)} scrapers passed")
    return True


def main():
    """Run all tests."""
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " OpportunityRadar System Tests ".center(58) + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    results = []

    results.append(("Imports", test_imports()))
    results.append(("DSL Engine", test_dsl_engine()))
    results.append(("Scorer", test_scorer()))
    results.append(("AI Prompts", test_ai_prompts()))
    results.append(("Scrapers", test_scrapers()))

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    failed = sum(1 for _, r in results if not r)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    print()
    print(f"Total: {passed} passed, {failed} failed")
    print()

    if failed == 0:
        print("🎉 All tests passed! System is ready.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
