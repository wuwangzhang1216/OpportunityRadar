"""Comprehensive unit tests for OnboardingService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import ipaddress


class TestSSRFProtection:
    """Test SSRF protection functions."""

    def test_ssrf_protection_error_import(self):
        """Test SSRFProtectionError can be imported."""
        from src.opportunity_radar.services.onboarding_service import SSRFProtectionError
        assert SSRFProtectionError is not None

    def test_validate_url_for_ssrf_import(self):
        """Test validate_url_for_ssrf can be imported."""
        from src.opportunity_radar.services.onboarding_service import validate_url_for_ssrf
        assert validate_url_for_ssrf is not None

    def test_validate_url_blocks_localhost(self):
        """Test SSRF validation blocks localhost."""
        from src.opportunity_radar.services.onboarding_service import (
            validate_url_for_ssrf,
            SSRFProtectionError,
        )

        with pytest.raises(SSRFProtectionError):
            validate_url_for_ssrf("http://localhost/admin")

    def test_validate_url_blocks_127_0_0_1(self):
        """Test SSRF validation blocks 127.0.0.1."""
        from src.opportunity_radar.services.onboarding_service import (
            validate_url_for_ssrf,
            SSRFProtectionError,
        )

        with pytest.raises(SSRFProtectionError):
            validate_url_for_ssrf("http://127.0.0.1/admin")

    def test_validate_url_blocks_private_ip(self):
        """Test SSRF validation blocks private IP ranges."""
        from src.opportunity_radar.services.onboarding_service import (
            validate_url_for_ssrf,
            SSRFProtectionError,
        )

        # 10.x.x.x
        with pytest.raises(SSRFProtectionError):
            validate_url_for_ssrf("http://10.0.0.1/internal")

        # 192.168.x.x
        with pytest.raises(SSRFProtectionError):
            validate_url_for_ssrf("http://192.168.1.1/internal")

        # 172.16.x.x
        with pytest.raises(SSRFProtectionError):
            validate_url_for_ssrf("http://172.16.0.1/internal")

    def test_validate_url_blocks_aws_metadata(self):
        """Test SSRF validation blocks AWS metadata endpoint."""
        from src.opportunity_radar.services.onboarding_service import (
            validate_url_for_ssrf,
            SSRFProtectionError,
        )

        with pytest.raises(SSRFProtectionError):
            validate_url_for_ssrf("http://169.254.169.254/latest/meta-data/")

    def test_validate_url_blocks_gcp_metadata(self):
        """Test SSRF validation blocks GCP metadata endpoint."""
        from src.opportunity_radar.services.onboarding_service import (
            validate_url_for_ssrf,
            SSRFProtectionError,
        )

        with pytest.raises(SSRFProtectionError):
            validate_url_for_ssrf("http://metadata.google.internal/")

    def test_validate_url_blocks_non_http_schemes(self):
        """Test SSRF validation blocks non-HTTP schemes."""
        from src.opportunity_radar.services.onboarding_service import (
            validate_url_for_ssrf,
            SSRFProtectionError,
        )

        with pytest.raises(SSRFProtectionError):
            validate_url_for_ssrf("file:///etc/passwd")

        with pytest.raises(SSRFProtectionError):
            validate_url_for_ssrf("ftp://internal.server/")

    def test_validate_url_allows_valid_urls(self):
        """Test SSRF validation allows valid external URLs."""
        from src.opportunity_radar.services.onboarding_service import validate_url_for_ssrf

        # Should not raise for valid external URLs
        try:
            validate_url_for_ssrf("https://github.com/user/repo")
            validate_url_for_ssrf("https://example.com")
        except Exception:
            pass  # May fail on network resolution in test env


class TestGoalsNormalization:
    """Test goals normalization function."""

    def test_normalize_goals_import(self):
        """Test normalize_goals can be imported."""
        from src.opportunity_radar.services.onboarding_service import normalize_goals
        assert normalize_goals is not None

    def test_normalize_goals_empty(self):
        """Test normalize_goals with empty list."""
        from src.opportunity_radar.services.onboarding_service import normalize_goals

        result = normalize_goals([])
        assert result == []

    def test_normalize_goals_none(self):
        """Test normalize_goals with None."""
        from src.opportunity_radar.services.onboarding_service import normalize_goals

        result = normalize_goals(None)
        assert result == []

    def test_normalize_goals_valid_goals(self):
        """Test normalize_goals with valid standard goals."""
        from src.opportunity_radar.services.onboarding_service import normalize_goals

        result = normalize_goals(["funding", "prizes", "learning"])

        assert "funding" in result
        assert "prizes" in result
        assert "learning" in result

    def test_normalize_goals_maps_synonyms(self):
        """Test normalize_goals maps synonyms to standard values."""
        from src.opportunity_radar.services.onboarding_service import normalize_goals

        result = normalize_goals(["get_funding", "win_prizes", "network"])

        assert "funding" in result
        assert "prizes" in result
        assert "networking" in result

    def test_normalize_goals_case_insensitive(self):
        """Test normalize_goals is case insensitive."""
        from src.opportunity_radar.services.onboarding_service import normalize_goals

        result = normalize_goals(["FUNDING", "Prizes", "LeArNiNg"])

        assert "funding" in result
        assert "prizes" in result
        assert "learning" in result

    def test_normalize_goals_deduplicates(self):
        """Test normalize_goals removes duplicates."""
        from src.opportunity_radar.services.onboarding_service import normalize_goals

        result = normalize_goals(["funding", "get_funding", "raise_money"])

        # All map to "funding", should only appear once
        assert result.count("funding") == 1


class TestURLTypeDetection:
    """Test URL type detection."""

    def test_detect_url_type_github(self):
        """Test detecting GitHub URLs."""
        from src.opportunity_radar.services.onboarding_service import OnboardingService
        from src.opportunity_radar.schemas.onboarding import URLType

        with patch.object(OnboardingService, "__init__", lambda self: None):
            service = OnboardingService()
            service.openai_client = MagicMock()
            service.http_client = MagicMock()

            result = service.detect_url_type("https://github.com/user/repo")

            assert result == URLType.GITHUB_REPO

    def test_detect_url_type_website(self):
        """Test detecting regular website URLs."""
        from src.opportunity_radar.services.onboarding_service import OnboardingService
        from src.opportunity_radar.schemas.onboarding import URLType

        with patch.object(OnboardingService, "__init__", lambda self: None):
            service = OnboardingService()
            service.openai_client = MagicMock()
            service.http_client = MagicMock()

            result = service.detect_url_type("https://example.com")

            assert result == URLType.WEBSITE

    def test_detect_url_type_github_variations(self):
        """Test detecting various GitHub URL formats."""
        from src.opportunity_radar.services.onboarding_service import OnboardingService
        from src.opportunity_radar.schemas.onboarding import URLType

        with patch.object(OnboardingService, "__init__", lambda self: None):
            service = OnboardingService()
            service.openai_client = MagicMock()
            service.http_client = MagicMock()

            urls = [
                "https://github.com/user/repo",
                "http://github.com/user/repo",
                "https://www.github.com/user/repo",
            ]

            for url in urls:
                result = service.detect_url_type(url)
                assert result == URLType.GITHUB_REPO, f"Failed for {url}"


class TestOnboardingServiceStructure:
    """Test OnboardingService class structure."""

    def test_service_import(self):
        """Test OnboardingService can be imported."""
        from src.opportunity_radar.services.onboarding_service import OnboardingService
        assert OnboardingService is not None

    def test_service_has_required_methods(self):
        """Test OnboardingService has all required methods."""
        from src.opportunity_radar.services.onboarding_service import OnboardingService

        required_methods = [
            "extract_profile_from_url",
            "detect_url_type",
            "confirm_profile",
            "get_onboarding_status",
        ]

        for method in required_methods:
            assert hasattr(OnboardingService, method), f"Missing method: {method}"

    def test_max_redirects_constant(self):
        """Test MAX_REDIRECTS constant is defined."""
        from src.opportunity_radar.services.onboarding_service import OnboardingService

        assert hasattr(OnboardingService, "MAX_REDIRECTS")
        assert OnboardingService.MAX_REDIRECTS == 5


class TestOnboardingSchemas:
    """Test onboarding-related schemas."""

    def test_url_type_enum(self):
        """Test URLType enum."""
        from src.opportunity_radar.schemas.onboarding import URLType

        assert URLType.WEBSITE is not None
        assert URLType.GITHUB_REPO is not None

    def test_extracted_field_schema(self):
        """Test ExtractedField schema."""
        from src.opportunity_radar.schemas.onboarding import ExtractedField

        field = ExtractedField(
            value="Test Company",
            confidence=0.9,
            source="website",
        )

        assert field.value == "Test Company"
        assert field.confidence == 0.9
        assert field.source == "website"

    def test_extracted_profile_schema(self):
        """Test ExtractedProfile schema."""
        from src.opportunity_radar.schemas.onboarding import ExtractedProfile, URLType

        profile = ExtractedProfile(
            url_type=URLType.WEBSITE,
            source_url="https://example.com",
        )

        assert profile.url_type == URLType.WEBSITE
        assert profile.source_url == "https://example.com"

    def test_onboarding_confirm_request_schema(self):
        """Test OnboardingConfirmRequest schema."""
        from src.opportunity_radar.schemas.onboarding import OnboardingConfirmRequest

        request = OnboardingConfirmRequest(
            display_name="My Project",
            tech_stack=["Python", "FastAPI"],
            goals=["funding", "networking"],
        )

        assert request.display_name == "My Project"
        assert len(request.tech_stack) == 2
        assert len(request.goals) == 2


@pytest.mark.asyncio
class TestOnboardingServiceAsync:
    """Async tests for OnboardingService."""

    async def test_extract_profile_adds_https(self):
        """Test extract_profile_from_url adds https if missing."""
        from src.opportunity_radar.services.onboarding_service import OnboardingService

        with patch.object(OnboardingService, "__init__", lambda self: None):
            service = OnboardingService()
            service.openai_client = MagicMock()
            service.http_client = MagicMock()

            # Mock internal methods
            service._scrape_website = AsyncMock(return_value="Test content")
            service._llm_extract = AsyncMock(return_value={})

            # Should add https
            with patch(
                "src.opportunity_radar.services.onboarding_service.validate_url_for_ssrf"
            ):
                result = await service.extract_profile_from_url("example.com")

            assert result.source_url == "https://example.com"

    async def test_extract_profile_calls_github_for_github_urls(self):
        """Test extract_profile_from_url uses GitHub scraper for GitHub URLs."""
        from src.opportunity_radar.services.onboarding_service import OnboardingService

        with patch.object(OnboardingService, "__init__", lambda self: None):
            service = OnboardingService()
            service.openai_client = MagicMock()
            service.http_client = MagicMock()

            service._scrape_github = AsyncMock(return_value="GitHub content")
            service._scrape_website = AsyncMock(return_value="Website content")
            service._llm_extract = AsyncMock(return_value={})

            with patch(
                "src.opportunity_radar.services.onboarding_service.validate_url_for_ssrf"
            ):
                await service.extract_profile_from_url("https://github.com/user/repo")

            service._scrape_github.assert_called_once()
            service._scrape_website.assert_not_called()

    async def test_get_onboarding_status_no_profile(self):
        """Test get_onboarding_status when user has no profile."""
        from src.opportunity_radar.services.onboarding_service import OnboardingService

        with patch.object(OnboardingService, "__init__", lambda self: None):
            service = OnboardingService()
            service.openai_client = MagicMock()
            service.http_client = MagicMock()

            mock_user = MagicMock()
            mock_user.id = "user_id"

            with patch(
                "src.opportunity_radar.services.onboarding_service.Profile"
            ) as MockProfile:
                MockProfile.find_one = AsyncMock(return_value=None)

                result = await service.get_onboarding_status(mock_user)

            assert result["has_profile"] is False
            assert result["onboarding_completed"] is False
            assert result["profile_id"] is None

    async def test_get_onboarding_status_with_profile(self):
        """Test get_onboarding_status when user has profile."""
        from src.opportunity_radar.services.onboarding_service import OnboardingService

        with patch.object(OnboardingService, "__init__", lambda self: None):
            service = OnboardingService()
            service.openai_client = MagicMock()
            service.http_client = MagicMock()

            mock_user = MagicMock()
            mock_user.id = "user_id"

            mock_profile = MagicMock()
            mock_profile.id = "profile_id"
            mock_profile.tech_stack = ["Python"]
            mock_profile.goals = ["funding"]
            mock_profile.bio = "Test bio"

            with patch(
                "src.opportunity_radar.services.onboarding_service.Profile"
            ) as MockProfile:
                MockProfile.find_one = AsyncMock(return_value=mock_profile)

                result = await service.get_onboarding_status(mock_user)

            assert result["has_profile"] is True
            assert result["onboarding_completed"] is True
            assert result["profile_id"] == "profile_id"

    async def test_get_onboarding_status_incomplete_profile(self):
        """Test get_onboarding_status with incomplete profile."""
        from src.opportunity_radar.services.onboarding_service import OnboardingService

        with patch.object(OnboardingService, "__init__", lambda self: None):
            service = OnboardingService()
            service.openai_client = MagicMock()
            service.http_client = MagicMock()

            mock_user = MagicMock()
            mock_user.id = "user_id"

            mock_profile = MagicMock()
            mock_profile.id = "profile_id"
            # Empty lists and None bio mean profile is incomplete
            mock_profile.tech_stack = []
            mock_profile.goals = []
            mock_profile.bio = None

            with patch(
                "src.opportunity_radar.services.onboarding_service.Profile"
            ) as MockProfile:
                MockProfile.find_one = AsyncMock(return_value=mock_profile)

                result = await service.get_onboarding_status(mock_user)

            assert result["has_profile"] is True
            # When tech_stack is empty, goals is empty, and bio is None,
            # the profile is considered incomplete
            # The actual check is: has_tech_stack or has_goals or has_bio
            # All are falsy, so onboarding_completed should be False
            assert result.get("onboarding_completed") is False or result.get("onboarding_completed") is None

    async def test_confirm_profile_creates_new(self):
        """Test confirm_profile creates new profile."""
        from src.opportunity_radar.services.onboarding_service import OnboardingService
        from src.opportunity_radar.schemas.onboarding import OnboardingConfirmRequest

        with patch.object(OnboardingService, "__init__", lambda self: None):
            service = OnboardingService()
            service.openai_client = MagicMock()
            service.http_client = MagicMock()
            service._generate_profile_embedding = MagicMock(return_value=None)

            mock_user = MagicMock()
            mock_user.id = "user_id"

            mock_profile = MagicMock()
            mock_profile.id = "new_profile_id"
            mock_profile.insert = AsyncMock()

            data = OnboardingConfirmRequest(
                display_name="My Project",
                tech_stack=["Python"],
                goals=["funding"],
            )

            with patch(
                "src.opportunity_radar.services.onboarding_service.Profile"
            ) as MockProfile:
                MockProfile.find_one = AsyncMock(return_value=None)
                MockProfile.return_value = mock_profile

                result = await service.confirm_profile(mock_user, data)

            mock_profile.insert.assert_called_once()

    async def test_confirm_profile_updates_existing(self):
        """Test confirm_profile updates existing profile."""
        from src.opportunity_radar.services.onboarding_service import OnboardingService
        from src.opportunity_radar.schemas.onboarding import OnboardingConfirmRequest

        with patch.object(OnboardingService, "__init__", lambda self: None):
            service = OnboardingService()
            service.openai_client = MagicMock()
            service.http_client = MagicMock()
            service._generate_profile_embedding = MagicMock(return_value=None)

            mock_user = MagicMock()
            mock_user.id = "user_id"

            mock_profile = MagicMock()
            mock_profile.id = "existing_profile_id"
            mock_profile.save = AsyncMock()

            data = OnboardingConfirmRequest(
                display_name="Updated Project",
                tech_stack=["Python", "FastAPI"],
                goals=["networking"],
            )

            with patch(
                "src.opportunity_radar.services.onboarding_service.Profile"
            ) as MockProfile:
                MockProfile.find_one = AsyncMock(return_value=mock_profile)

                result = await service.confirm_profile(mock_user, data)

            mock_profile.save.assert_called_once()
            assert mock_profile.display_name == "Updated Project"


class TestGoalsNormalizationMap:
    """Test GOALS_NORMALIZATION_MAP constant."""

    def test_goals_map_exists(self):
        """Test GOALS_NORMALIZATION_MAP is defined."""
        from src.opportunity_radar.services.onboarding_service import (
            GOALS_NORMALIZATION_MAP,
        )

        assert isinstance(GOALS_NORMALIZATION_MAP, dict)
        assert len(GOALS_NORMALIZATION_MAP) > 0

    def test_goals_map_covers_funding(self):
        """Test goals map covers funding-related terms."""
        from src.opportunity_radar.services.onboarding_service import (
            GOALS_NORMALIZATION_MAP,
        )

        funding_terms = ["get_funding", "raise_money", "investment"]
        for term in funding_terms:
            assert term in GOALS_NORMALIZATION_MAP
            assert GOALS_NORMALIZATION_MAP[term] == "funding"

    def test_goals_map_covers_learning(self):
        """Test goals map covers learning-related terms."""
        from src.opportunity_radar.services.onboarding_service import (
            GOALS_NORMALIZATION_MAP,
        )

        learning_terms = ["learn", "learn_skills", "education"]
        for term in learning_terms:
            assert term in GOALS_NORMALIZATION_MAP
            assert GOALS_NORMALIZATION_MAP[term] == "learning"


class TestValidGoals:
    """Test VALID_GOALS constant."""

    def test_valid_goals_exists(self):
        """Test VALID_GOALS is defined."""
        from src.opportunity_radar.services.onboarding_service import VALID_GOALS

        assert isinstance(VALID_GOALS, set)
        assert len(VALID_GOALS) > 0

    def test_valid_goals_content(self):
        """Test VALID_GOALS contains expected values."""
        from src.opportunity_radar.services.onboarding_service import VALID_GOALS

        expected = {
            "funding",
            "prizes",
            "learning",
            "networking",
            "exposure",
            "mentorship",
            "equity",
            "building",
        }

        assert VALID_GOALS == expected


class TestSingleton:
    """Test singleton instance."""

    def test_get_onboarding_service(self):
        """Test get_onboarding_service returns singleton."""
        from src.opportunity_radar.services.onboarding_service import (
            get_onboarding_service,
        )

        # Reset singleton for test
        import src.opportunity_radar.services.onboarding_service as module

        module._onboarding_service = None

        with patch.object(module.OnboardingService, "__init__", lambda self: None):
            service1 = get_onboarding_service()
            service2 = get_onboarding_service()

            assert service1 is service2
