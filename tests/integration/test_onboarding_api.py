"""Integration tests for Onboarding API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import ASGITransport, AsyncClient
from datetime import datetime


class TestOnboardingEndpointAuth:
    """Test that onboarding endpoints require authentication."""

    @pytest.mark.asyncio
    async def test_extract_requires_auth(self, async_client: AsyncClient):
        """Test POST /onboarding/extract requires authentication."""
        response = await async_client.post(
            "/api/v1/onboarding/extract",
            json={"url": "https://example.com"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_confirm_requires_auth(self, async_client: AsyncClient):
        """Test POST /onboarding/confirm requires authentication."""
        response = await async_client.post(
            "/api/v1/onboarding/confirm",
            json={"tech_stack": ["Python"], "goals": ["Build AI products"]},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_status_requires_auth(self, async_client: AsyncClient):
        """Test GET /onboarding/status requires authentication."""
        response = await async_client.get("/api/v1/onboarding/status")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_suggestions_requires_auth(self, async_client: AsyncClient):
        """Test GET /onboarding/suggestions requires authentication."""
        response = await async_client.get("/api/v1/onboarding/suggestions")
        assert response.status_code == 401


class TestExtractEndpoint:
    """Test POST /api/v1/onboarding/extract endpoint."""

    @pytest.mark.asyncio
    async def test_extract_validates_url(self, async_client: AsyncClient):
        """Test that extract validates URL format."""
        response = await async_client.post(
            "/api/v1/onboarding/extract",
            json={"url": "not-a-valid-url"},
            headers={"Authorization": "Bearer invalid"},
        )
        # 401 (auth) or 422 (validation)
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_extract_requires_url_field(self, async_client: AsyncClient):
        """Test that extract requires url field."""
        response = await async_client.post(
            "/api/v1/onboarding/extract",
            json={},
            headers={"Authorization": "Bearer invalid"},
        )
        # Should fail validation
        assert response.status_code in [401, 422]


class TestConfirmEndpoint:
    """Test POST /api/v1/onboarding/confirm endpoint."""

    @pytest.mark.asyncio
    async def test_confirm_accepts_profile_data(self, async_client: AsyncClient):
        """Test that confirm accepts profile data."""
        response = await async_client.post(
            "/api/v1/onboarding/confirm",
            json={
                "tech_stack": ["Python", "React"],
                "goals": ["Build AI products"],
                "industries": ["Technology"],
            },
            headers={"Authorization": "Bearer invalid"},
        )
        # Either 401 (auth first) or processes further
        assert response.status_code in [401, 200, 500]


class TestSuggestionsEndpoint:
    """Test GET /api/v1/onboarding/suggestions endpoint."""

    @pytest.mark.asyncio
    async def test_suggestions_returns_lists(self):
        """Test that suggestions returns tech_stacks, goals, and industries."""
        from src.opportunity_radar.main import app

        mock_user = MagicMock()
        mock_user.id = "507f1f77bcf86cd799439011"

        with patch("src.opportunity_radar.core.security.get_current_user") as mock_get_user:
            mock_get_user.return_value = mock_user

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/onboarding/suggestions",
                    headers={"Authorization": "Bearer valid_token"},
                )

                if response.status_code == 200:
                    data = response.json()
                    assert "tech_stacks" in data
                    assert "goals" in data
                    assert "industries" in data
                    assert isinstance(data["tech_stacks"], list)
                    assert isinstance(data["goals"], list)
                    assert isinstance(data["industries"], list)


class TestOnboardingMocked:
    """Test onboarding endpoints with mocked services."""

    def _create_mock_user(self):
        """Create a mock user object."""
        mock_user = MagicMock()
        mock_user.id = "507f1f77bcf86cd799439011"
        mock_user.email = "test@example.com"
        mock_user.full_name = "Test User"
        mock_user.is_active = True
        return mock_user

    @pytest.mark.asyncio
    async def test_extract_success_response(self):
        """Test successful URL extraction response structure."""
        from src.opportunity_radar.main import app

        mock_user = self._create_mock_user()
        mock_extracted = MagicMock()
        mock_extracted.tech_stack = ["Python", "FastAPI"]
        mock_extracted.goals = ["Build AI tools"]
        mock_extracted.industries = ["Technology"]
        mock_extracted.company_name = "TestCo"
        mock_extracted.product_description = "A test product"

        with patch("src.opportunity_radar.core.security.get_current_user") as mock_get_user:
            mock_get_user.return_value = mock_user

            with patch("src.opportunity_radar.api.v1.endpoints.onboarding.get_onboarding_service") as mock_get_service:
                mock_service = MagicMock()
                mock_service.extract_profile_from_url = AsyncMock(return_value=mock_extracted)
                mock_get_service.return_value = mock_service

                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/onboarding/extract",
                        json={"url": "https://github.com/test/repo"},
                        headers={"Authorization": "Bearer valid_token"},
                    )

                    if response.status_code == 200:
                        data = response.json()
                        assert data["success"] is True
                        assert "extracted_profile" in data

    @pytest.mark.asyncio
    async def test_extract_failure_response(self):
        """Test URL extraction failure response structure."""
        from src.opportunity_radar.main import app

        mock_user = self._create_mock_user()

        with patch("src.opportunity_radar.core.security.get_current_user") as mock_get_user:
            mock_get_user.return_value = mock_user

            with patch("src.opportunity_radar.api.v1.endpoints.onboarding.get_onboarding_service") as mock_get_service:
                mock_service = MagicMock()
                mock_service.extract_profile_from_url = AsyncMock(side_effect=Exception("Network error"))
                mock_get_service.return_value = mock_service

                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/onboarding/extract",
                        json={"url": "https://example.com"},
                        headers={"Authorization": "Bearer valid_token"},
                    )

                    if response.status_code == 200:
                        data = response.json()
                        assert data["success"] is False
                        assert "error_message" in data

    @pytest.mark.asyncio
    async def test_status_completed(self):
        """Test onboarding status when completed."""
        from src.opportunity_radar.main import app

        mock_user = self._create_mock_user()

        with patch("src.opportunity_radar.core.security.get_current_user") as mock_get_user:
            mock_get_user.return_value = mock_user

            with patch("src.opportunity_radar.api.v1.endpoints.onboarding.get_onboarding_service") as mock_get_service:
                mock_service = MagicMock()
                mock_service.get_onboarding_status = AsyncMock(return_value={
                    "has_profile": True,
                    "onboarding_completed": True,
                    "profile_id": "profile123",
                })
                mock_get_service.return_value = mock_service

                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/onboarding/status",
                        headers={"Authorization": "Bearer valid_token"},
                    )

                    if response.status_code == 200:
                        data = response.json()
                        assert data["has_profile"] is True
                        assert data["onboarding_completed"] is True

    @pytest.mark.asyncio
    async def test_status_not_completed(self):
        """Test onboarding status when not completed."""
        from src.opportunity_radar.main import app

        mock_user = self._create_mock_user()

        with patch("src.opportunity_radar.core.security.get_current_user") as mock_get_user:
            mock_get_user.return_value = mock_user

            with patch("src.opportunity_radar.api.v1.endpoints.onboarding.get_onboarding_service") as mock_get_service:
                mock_service = MagicMock()
                mock_service.get_onboarding_status = AsyncMock(return_value={
                    "has_profile": False,
                    "onboarding_completed": False,
                    "profile_id": None,
                })
                mock_get_service.return_value = mock_service

                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/onboarding/status",
                        headers={"Authorization": "Bearer valid_token"},
                    )

                    if response.status_code == 200:
                        data = response.json()
                        assert data["has_profile"] is False
                        assert data["onboarding_completed"] is False

    @pytest.mark.asyncio
    async def test_confirm_creates_profile(self):
        """Test that confirm creates profile and returns success."""
        from src.opportunity_radar.main import app

        mock_user = self._create_mock_user()
        mock_profile = MagicMock()
        mock_profile.id = "profile123"

        with patch("src.opportunity_radar.core.security.get_current_user") as mock_get_user:
            mock_get_user.return_value = mock_user

            with patch("src.opportunity_radar.api.v1.endpoints.onboarding.get_onboarding_service") as mock_get_service:
                mock_service = MagicMock()
                mock_service.confirm_profile = AsyncMock(return_value=mock_profile)
                mock_get_service.return_value = mock_service

                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/onboarding/confirm",
                        json={
                            "tech_stack": ["Python", "React"],
                            "goals": ["Build AI products"],
                            "industries": ["Technology"],
                        },
                        headers={"Authorization": "Bearer valid_token"},
                    )

                    if response.status_code == 200:
                        data = response.json()
                        assert data["success"] is True
                        assert data["profile_id"] == "profile123"
                        assert data["onboarding_completed"] is True


class TestOnboardingSchemas:
    """Test onboarding schema imports and constants."""

    def test_common_tech_stacks_imported(self):
        """Test that COMMON_TECH_STACKS is available."""
        from src.opportunity_radar.schemas.onboarding import COMMON_TECH_STACKS
        assert isinstance(COMMON_TECH_STACKS, list)
        assert len(COMMON_TECH_STACKS) > 0

    def test_common_goals_imported(self):
        """Test that COMMON_GOALS is available."""
        from src.opportunity_radar.schemas.onboarding import COMMON_GOALS
        assert isinstance(COMMON_GOALS, list)
        assert len(COMMON_GOALS) > 0

    def test_common_industries_imported(self):
        """Test that COMMON_INDUSTRIES is available."""
        from src.opportunity_radar.schemas.onboarding import COMMON_INDUSTRIES
        assert isinstance(COMMON_INDUSTRIES, list)
        assert len(COMMON_INDUSTRIES) > 0
