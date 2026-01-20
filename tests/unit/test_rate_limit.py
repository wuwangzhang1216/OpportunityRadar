"""Unit tests for rate limiting functionality."""

import pytest


class TestRateLimitConfig:
    """Test rate limit configuration."""

    def test_import_limiter(self):
        """Test limiter import."""
        from src.opportunity_radar.core.rate_limit import limiter

        assert limiter is not None

    def test_import_rate_limits(self):
        """Test RateLimits import."""
        from src.opportunity_radar.core.rate_limit import RateLimits

        assert RateLimits is not None

    def test_auth_rate_limits_defined(self):
        """Test authentication rate limits are defined."""
        from src.opportunity_radar.core.rate_limit import RateLimits

        assert hasattr(RateLimits, "AUTH_LOGIN")
        assert hasattr(RateLimits, "AUTH_SIGNUP")
        assert hasattr(RateLimits, "AUTH_PASSWORD_RESET")

    def test_api_rate_limits_defined(self):
        """Test API rate limits are defined."""
        from src.opportunity_radar.core.rate_limit import RateLimits

        assert hasattr(RateLimits, "API_STANDARD")
        assert hasattr(RateLimits, "API_SEARCH")

    def test_ai_rate_limits_defined(self):
        """Test AI rate limits are defined."""
        from src.opportunity_radar.core.rate_limit import RateLimits

        assert hasattr(RateLimits, "AI_GENERATE")
        assert hasattr(RateLimits, "AI_EMBEDDING")

    def test_rate_limit_format(self):
        """Test rate limit format is valid."""
        from src.opportunity_radar.core.rate_limit import RateLimits

        # Rate limits should be in format "N/period"
        assert "/" in RateLimits.AUTH_LOGIN
        assert "/" in RateLimits.API_STANDARD

    def test_auth_limits_are_stricter(self):
        """Test authentication limits are stricter than standard API."""
        from src.opportunity_radar.core.rate_limit import RateLimits

        # Parse the numbers from rate limit strings
        def get_limit_number(limit_str: str) -> int:
            return int(limit_str.split("/")[0])

        auth_limit = get_limit_number(RateLimits.AUTH_LOGIN)
        api_limit = get_limit_number(RateLimits.API_STANDARD)

        # Auth should be more restrictive
        assert auth_limit < api_limit


class TestRateLimitExceededHandler:
    """Test rate limit exceeded handler."""

    def test_import_handler(self):
        """Test rate_limit_exceeded_handler import."""
        from src.opportunity_radar.core.rate_limit import rate_limit_exceeded_handler

        assert rate_limit_exceeded_handler is not None
        assert callable(rate_limit_exceeded_handler)


class TestClientIPExtraction:
    """Test client IP extraction for rate limiting."""

    def test_import_get_client_ip(self):
        """Test get_client_ip import."""
        from src.opportunity_radar.core.rate_limit import get_client_ip

        assert get_client_ip is not None
        assert callable(get_client_ip)
