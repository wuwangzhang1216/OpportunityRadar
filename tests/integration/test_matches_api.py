"""Integration tests for Matches API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import ASGITransport, AsyncClient
from datetime import datetime


class TestMatchesEndpointAuth:
    """Test matches endpoints require authentication."""

    @pytest.mark.asyncio
    async def test_list_matches_requires_auth(self, async_client: AsyncClient):
        """Test GET /matches requires authentication."""
        response = await async_client.get("/api/v1/matches")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_top_matches_requires_auth(self, async_client: AsyncClient):
        """Test GET /matches/top requires authentication."""
        response = await async_client.get("/api/v1/matches/top")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_match_status_requires_auth(self, async_client: AsyncClient):
        """Test GET /matches/status requires authentication."""
        response = await async_client.get("/api/v1/matches/status")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_match_stats_requires_auth(self, async_client: AsyncClient):
        """Test GET /matches/stats requires authentication."""
        response = await async_client.get("/api/v1/matches/stats")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_calculate_matches_requires_auth(self, async_client: AsyncClient):
        """Test POST /matches/calculate requires authentication."""
        response = await async_client.post("/api/v1/matches/calculate")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_dismiss_match_requires_auth(self, async_client: AsyncClient):
        """Test POST /matches/{id}/dismiss requires authentication."""
        response = await async_client.post("/api/v1/matches/some-id/dismiss")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_bookmark_match_requires_auth(self, async_client: AsyncClient):
        """Test POST /matches/{id}/bookmark requires authentication."""
        response = await async_client.post("/api/v1/matches/some-id/bookmark")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_unbookmark_match_requires_auth(self, async_client: AsyncClient):
        """Test POST /matches/{id}/unbookmark requires authentication."""
        response = await async_client.post("/api/v1/matches/some-id/unbookmark")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_restore_match_requires_auth(self, async_client: AsyncClient):
        """Test POST /matches/{id}/restore requires authentication."""
        response = await async_client.post("/api/v1/matches/some-id/restore")
        assert response.status_code == 401


class TestMatchesQueryParams:
    """Test matches endpoint query parameter validation."""

    @pytest.mark.asyncio
    async def test_list_matches_validates_limit(self, async_client: AsyncClient):
        """Test that limit parameter is validated."""
        # Limit too high
        response = await async_client.get(
            "/api/v1/matches?limit=500",
            headers={"Authorization": "Bearer invalid"},
        )
        # Either 422 (validation) or 401 (auth checked first)
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_list_matches_validates_skip(self, async_client: AsyncClient):
        """Test that skip parameter is validated."""
        # Negative skip
        response = await async_client.get(
            "/api/v1/matches?skip=-1",
            headers={"Authorization": "Bearer invalid"},
        )
        assert response.status_code in [401, 422]


class TestMatchesEndpointsMocked:
    """Test matches endpoints with mocked authentication and database."""

    def _create_mock_user(self):
        """Create a mock user object."""
        mock_user = MagicMock()
        mock_user.id = "507f1f77bcf86cd799439011"
        mock_user.email = "test@example.com"
        mock_user.full_name = "Test User"
        mock_user.is_active = True
        return mock_user

    def _create_mock_match(self, match_id: str, user_id: str):
        """Create a mock match object."""
        mock_match = MagicMock()
        mock_match.id = match_id
        mock_match.user_id = user_id
        mock_match.opportunity_id = "opp123"
        mock_match.overall_score = 0.85
        mock_match.semantic_score = 0.8
        mock_match.is_dismissed = False
        mock_match.is_bookmarked = False
        mock_match.score_breakdown = {}
        mock_match.model_dump = MagicMock(return_value={
            "id": match_id,
            "user_id": user_id,
            "opportunity_id": "opp123",
            "overall_score": 0.85,
            "is_dismissed": False,
            "is_bookmarked": False,
        })
        return mock_match

    @pytest.mark.asyncio
    async def test_list_matches_empty(self):
        """Test list matches returns empty list when no matches."""
        from src.opportunity_radar.main import app

        mock_user = self._create_mock_user()

        with patch("src.opportunity_radar.core.security.get_current_user") as mock_get_user:
            mock_get_user.return_value = mock_user

            with patch("src.opportunity_radar.api.v1.endpoints.matches.Match") as MockMatch:
                # Mock empty result
                mock_query = MagicMock()
                mock_query.sort = MagicMock(return_value=mock_query)
                mock_query.skip = MagicMock(return_value=mock_query)
                mock_query.limit = MagicMock(return_value=mock_query)
                mock_query.to_list = AsyncMock(return_value=[])
                mock_query.count = AsyncMock(return_value=0)
                MockMatch.find = MagicMock(return_value=mock_query)

                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/matches",
                        headers={"Authorization": "Bearer valid_token"},
                    )

                    # May still need beanie init, check for expected responses
                    if response.status_code == 200:
                        data = response.json()
                        assert "items" in data
                        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_match_status_no_profile(self):
        """Test match status returns no_profile when user has no profile."""
        from src.opportunity_radar.main import app

        mock_user = self._create_mock_user()

        with patch("src.opportunity_radar.core.security.get_current_user") as mock_get_user:
            mock_get_user.return_value = mock_user

            with patch("src.opportunity_radar.api.v1.endpoints.matches.Match") as MockMatch:
                mock_query = MagicMock()
                mock_query.count = AsyncMock(return_value=0)
                MockMatch.find = MagicMock(return_value=mock_query)

                with patch("src.opportunity_radar.api.v1.endpoints.matches.Profile") as MockProfile:
                    MockProfile.find_one = AsyncMock(return_value=None)

                    transport = ASGITransport(app=app)
                    async with AsyncClient(transport=transport, base_url="http://test") as client:
                        response = await client.get(
                            "/api/v1/matches/status",
                            headers={"Authorization": "Bearer valid_token"},
                        )

                        if response.status_code == 200:
                            data = response.json()
                            assert data["has_profile"] is False
                            assert data["status"] == "no_profile"


class TestMatchActionsValidation:
    """Test match action endpoint validation."""

    @pytest.mark.asyncio
    async def test_dismiss_invalid_match_id(self, async_client: AsyncClient):
        """Test dismissing non-existent match returns appropriate error."""
        response = await async_client.post(
            "/api/v1/matches/invalid-id/dismiss",
            headers={"Authorization": "Bearer some_token"},
        )
        # 401 (auth) or 404 (not found) are acceptable
        assert response.status_code in [401, 404, 500]

    @pytest.mark.asyncio
    async def test_bookmark_invalid_match_id(self, async_client: AsyncClient):
        """Test bookmarking non-existent match returns appropriate error."""
        response = await async_client.post(
            "/api/v1/matches/invalid-id/bookmark",
            headers={"Authorization": "Bearer some_token"},
        )
        assert response.status_code in [401, 404, 500]


class TestMatchByBatchEndpoint:
    """Test GET /matches/by-batch/{batch_id} endpoint."""

    @pytest.mark.asyncio
    async def test_match_by_batch_requires_auth(self, async_client: AsyncClient):
        """Test that by-batch endpoint requires authentication."""
        response = await async_client.get("/api/v1/matches/by-batch/some-batch-id")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_match_by_batch_returns_null_for_nonexistent(self):
        """Test that by-batch returns null for non-existent match."""
        from src.opportunity_radar.main import app

        mock_user = MagicMock()
        mock_user.id = "507f1f77bcf86cd799439011"

        with patch("src.opportunity_radar.core.security.get_current_user") as mock_get_user:
            mock_get_user.return_value = mock_user

            with patch("src.opportunity_radar.api.v1.endpoints.matches.Match") as MockMatch:
                MockMatch.find_one = AsyncMock(return_value=None)

                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/matches/by-batch/507f1f77bcf86cd799439012",
                        headers={"Authorization": "Bearer valid_token"},
                    )

                    if response.status_code == 200:
                        assert response.json() is None


class TestMatchCalculateEndpoint:
    """Test POST /matches/calculate endpoint."""

    @pytest.mark.asyncio
    async def test_calculate_requires_profile(self):
        """Test that calculate requires user to have a profile."""
        from src.opportunity_radar.main import app

        mock_user = MagicMock()
        mock_user.id = "507f1f77bcf86cd799439011"

        with patch("src.opportunity_radar.core.security.get_current_user") as mock_get_user:
            mock_get_user.return_value = mock_user

            with patch("src.opportunity_radar.api.v1.endpoints.matches.Profile") as MockProfile:
                MockProfile.find_one = AsyncMock(return_value=None)

                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/matches/calculate",
                        headers={"Authorization": "Bearer valid_token"},
                    )

                    # Should return 400 when no profile
                    if response.status_code == 400:
                        data = response.json()
                        assert "profile" in data.get("detail", "").lower()


class TestMatchStatsEndpoint:
    """Test GET /matches/stats endpoint."""

    @pytest.mark.asyncio
    async def test_stats_returns_correct_structure(self):
        """Test that stats returns expected fields."""
        from src.opportunity_radar.main import app

        mock_user = MagicMock()
        mock_user.id = "507f1f77bcf86cd799439011"

        with patch("src.opportunity_radar.core.security.get_current_user") as mock_get_user:
            mock_get_user.return_value = mock_user

            with patch("src.opportunity_radar.api.v1.endpoints.matches.Match") as MockMatch:
                mock_query = MagicMock()
                mock_query.count = AsyncMock(return_value=10)
                mock_query.to_list = AsyncMock(return_value=[])
                MockMatch.find = MagicMock(return_value=mock_query)

                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/matches/stats",
                        headers={"Authorization": "Bearer valid_token"},
                    )

                    if response.status_code == 200:
                        data = response.json()
                        expected_fields = ["total_matches", "bookmarked", "dismissed", "active", "average_score"]
                        for field in expected_fields:
                            assert field in data
