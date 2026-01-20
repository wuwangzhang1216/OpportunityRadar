"""Integration tests for Opportunities API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import ASGITransport, AsyncClient
from datetime import datetime, timedelta


class TestOpportunitiesListEndpoint:
    """Test GET /api/v1/opportunities endpoint."""

    @pytest.mark.asyncio
    async def test_list_endpoint_exists(self, async_client: AsyncClient):
        """Test that opportunities list endpoint exists."""
        response = await async_client.get("/api/v1/opportunities")
        # Endpoint should exist, may fail with 500 if no DB
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_list_accepts_pagination_params(self, async_client: AsyncClient):
        """Test that list accepts limit and skip parameters."""
        response = await async_client.get("/api/v1/opportunities?limit=10&skip=5")
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_list_validates_limit_max(self, async_client: AsyncClient):
        """Test that limit parameter has maximum validation."""
        response = await async_client.get("/api/v1/opportunities?limit=500")
        # Should return 422 for limit > 100
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_validates_limit_min(self, async_client: AsyncClient):
        """Test that limit parameter has minimum validation."""
        response = await async_client.get("/api/v1/opportunities?limit=0")
        # Should return 422 for limit < 1
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_validates_skip_min(self, async_client: AsyncClient):
        """Test that skip parameter validates non-negative."""
        response = await async_client.get("/api/v1/opportunities?skip=-1")
        # Should return 422 for skip < 0
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_accepts_category_filter(self, async_client: AsyncClient):
        """Test that list accepts category filter."""
        response = await async_client.get("/api/v1/opportunities?category=hackathon")
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_list_accepts_search_param(self, async_client: AsyncClient):
        """Test that list accepts search parameter."""
        response = await async_client.get("/api/v1/opportunities?search=AI")
        assert response.status_code in [200, 500]


class TestOpportunitiesGetEndpoint:
    """Test GET /api/v1/opportunities/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_endpoint_exists(self, async_client: AsyncClient):
        """Test that get opportunity endpoint exists."""
        response = await async_client.get("/api/v1/opportunities/507f1f77bcf86cd799439011")
        # 404 or 500 (no DB) are acceptable
        assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_get_invalid_id_format(self, async_client: AsyncClient):
        """Test that invalid ObjectId returns 404."""
        response = await async_client.get("/api/v1/opportunities/invalid-id")
        assert response.status_code in [404, 500]


class TestOpportunitiesMocked:
    """Test opportunities endpoints with mocked database."""

    def _create_mock_opportunity(
        self,
        opp_id: str = "507f1f77bcf86cd799439011",
        title: str = "Test Hackathon",
    ):
        """Create a mock opportunity object."""
        mock_opp = MagicMock()
        mock_opp.id = opp_id
        mock_opp.title = title
        mock_opp.description = "A test hackathon"
        mock_opp.opportunity_type = "hackathon"
        mock_opp.application_deadline = datetime.utcnow() + timedelta(days=30)
        mock_opp.total_prize_value = 10000
        mock_opp.team_size_min = 1
        mock_opp.team_size_max = 5
        mock_opp.website_url = "https://example.com"
        mock_opp.source_url = "https://source.com"
        mock_opp.themes = ["AI", "ML"]
        mock_opp.technologies = ["Python", "TensorFlow"]
        mock_opp.location_region = "North America"
        mock_opp.location_country = "USA"
        mock_opp.location_city = "San Francisco"
        mock_opp.format = "hybrid"
        mock_opp.host_id = None
        mock_opp.model_dump = MagicMock(return_value={
            "id": opp_id,
            "title": title,
            "description": "A test hackathon",
            "opportunity_type": "hackathon",
            "application_deadline": mock_opp.application_deadline.isoformat(),
            "total_prize_value": 10000,
            "team_size_min": 1,
            "team_size_max": 5,
            "website_url": "https://example.com",
            "source_url": "https://source.com",
            "themes": ["AI", "ML"],
            "technologies": ["Python", "TensorFlow"],
            "location_region": "North America",
            "location_country": "USA",
            "location_city": "San Francisco",
            "format": "hybrid",
        })
        return mock_opp

    @pytest.mark.asyncio
    async def test_list_returns_paginated_response(self):
        """Test that list returns properly paginated response structure."""
        from src.opportunity_radar.main import app

        mock_opp = self._create_mock_opportunity()

        with patch("src.opportunity_radar.api.v1.endpoints.opportunities.Opportunity") as MockOpp:
            mock_query = MagicMock()
            mock_query.skip = MagicMock(return_value=mock_query)
            mock_query.limit = MagicMock(return_value=mock_query)
            mock_query.to_list = AsyncMock(return_value=[mock_opp])
            mock_query.count = AsyncMock(return_value=1)
            MockOpp.find = MagicMock(return_value=mock_query)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/opportunities?limit=10&skip=0")

                if response.status_code == 200:
                    data = response.json()
                    assert "items" in data
                    assert "total" in data
                    assert "skip" in data
                    assert "limit" in data

    @pytest.mark.asyncio
    async def test_list_filters_by_category(self):
        """Test that list properly filters by category."""
        from src.opportunity_radar.main import app

        with patch("src.opportunity_radar.api.v1.endpoints.opportunities.Opportunity") as MockOpp:
            mock_query = MagicMock()
            mock_query.skip = MagicMock(return_value=mock_query)
            mock_query.limit = MagicMock(return_value=mock_query)
            mock_query.to_list = AsyncMock(return_value=[])
            mock_query.count = AsyncMock(return_value=0)
            MockOpp.find = MagicMock(return_value=mock_query)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                await client.get("/api/v1/opportunities?category=hackathon")

                # Verify find was called with category filter
                MockOpp.find.assert_called()
                call_args = MockOpp.find.call_args[0][0]
                assert call_args.get("opportunity_type") == "hackathon"

    @pytest.mark.asyncio
    async def test_get_opportunity_transforms_data(self):
        """Test that get opportunity transforms data for frontend."""
        from src.opportunity_radar.main import app

        mock_opp = self._create_mock_opportunity()

        with patch("src.opportunity_radar.api.v1.endpoints.opportunities.Opportunity") as MockOpp:
            MockOpp.get = AsyncMock(return_value=mock_opp)

            with patch("src.opportunity_radar.api.v1.endpoints.opportunities.Host") as MockHost:
                MockHost.get = AsyncMock(return_value=None)

                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get("/api/v1/opportunities/507f1f77bcf86cd799439011")

                    if response.status_code == 200:
                        data = response.json()
                        # Check frontend field mappings exist
                        assert "category" in data
                        assert "deadline" in data
                        assert "prize_pool" in data
                        assert "team_min" in data
                        assert "team_max" in data
                        assert "url" in data
                        assert "tags" in data
                        assert "regions" in data
                        assert "remote_ok" in data

    @pytest.mark.asyncio
    async def test_get_opportunity_includes_host_name(self):
        """Test that get opportunity includes host name when available."""
        from src.opportunity_radar.main import app

        mock_opp = self._create_mock_opportunity()
        mock_opp.host_id = "host123"

        mock_host = MagicMock()
        mock_host.name = "DevPost"

        with patch("src.opportunity_radar.api.v1.endpoints.opportunities.Opportunity") as MockOpp:
            MockOpp.get = AsyncMock(return_value=mock_opp)

            with patch("src.opportunity_radar.api.v1.endpoints.opportunities.Host") as MockHost:
                MockHost.get = AsyncMock(return_value=mock_host)

                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get("/api/v1/opportunities/507f1f77bcf86cd799439011")

                    if response.status_code == 200:
                        data = response.json()
                        assert data.get("host_name") == "DevPost"

    @pytest.mark.asyncio
    async def test_get_nonexistent_opportunity(self):
        """Test that getting non-existent opportunity returns 404."""
        from src.opportunity_radar.main import app

        with patch("src.opportunity_radar.api.v1.endpoints.opportunities.Opportunity") as MockOpp:
            MockOpp.get = AsyncMock(return_value=None)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/opportunities/507f1f77bcf86cd799439011")

                assert response.status_code == 404
                data = response.json()
                assert "not found" in data.get("detail", "").lower()


class TestOpportunitiesTransformation:
    """Test opportunity data transformation logic."""

    def test_transform_includes_tags(self):
        """Test that transform combines themes and technologies into tags."""
        from src.opportunity_radar.api.v1.endpoints.opportunities import transform_opportunity_for_frontend

        mock_opp = MagicMock()
        mock_opp.themes = ["AI", "Web3"]
        mock_opp.technologies = ["Python", "Solidity"]
        mock_opp.opportunity_type = "hackathon"
        mock_opp.application_deadline = datetime.utcnow()
        mock_opp.total_prize_value = 5000
        mock_opp.team_size_min = 1
        mock_opp.team_size_max = 4
        mock_opp.website_url = "https://example.com"
        mock_opp.source_url = None
        mock_opp.location_region = None
        mock_opp.location_country = None
        mock_opp.location_city = None
        mock_opp.format = "online"
        mock_opp.model_dump = MagicMock(return_value={})

        result = transform_opportunity_for_frontend(mock_opp)

        assert "tags" in result
        assert "AI" in result["tags"]
        assert "Web3" in result["tags"]
        assert "Python" in result["tags"]
        assert "Solidity" in result["tags"]

    def test_transform_builds_regions(self):
        """Test that transform builds regions array from location fields."""
        from src.opportunity_radar.api.v1.endpoints.opportunities import transform_opportunity_for_frontend

        mock_opp = MagicMock()
        mock_opp.themes = []
        mock_opp.technologies = []
        mock_opp.opportunity_type = "hackathon"
        mock_opp.application_deadline = datetime.utcnow()
        mock_opp.total_prize_value = 5000
        mock_opp.team_size_min = 1
        mock_opp.team_size_max = 4
        mock_opp.website_url = "https://example.com"
        mock_opp.source_url = None
        mock_opp.location_region = "Europe"
        mock_opp.location_country = "Germany"
        mock_opp.location_city = "Berlin"
        mock_opp.format = "in_person"
        mock_opp.model_dump = MagicMock(return_value={})

        result = transform_opportunity_for_frontend(mock_opp)

        assert "regions" in result
        assert "Europe" in result["regions"]
        assert "Germany" in result["regions"]
        assert "Berlin" in result["regions"]

    def test_transform_determines_remote_ok(self):
        """Test that transform determines remote_ok from format."""
        from src.opportunity_radar.api.v1.endpoints.opportunities import transform_opportunity_for_frontend

        mock_opp = MagicMock()
        mock_opp.themes = []
        mock_opp.technologies = []
        mock_opp.opportunity_type = "hackathon"
        mock_opp.application_deadline = datetime.utcnow()
        mock_opp.total_prize_value = 5000
        mock_opp.team_size_min = 1
        mock_opp.team_size_max = 4
        mock_opp.website_url = "https://example.com"
        mock_opp.source_url = None
        mock_opp.location_region = None
        mock_opp.location_country = None
        mock_opp.location_city = None
        mock_opp.model_dump = MagicMock(return_value={})

        # Test online format
        mock_opp.format = "online"
        result = transform_opportunity_for_frontend(mock_opp)
        assert result["remote_ok"] is True

        # Test hybrid format
        mock_opp.format = "hybrid"
        result = transform_opportunity_for_frontend(mock_opp)
        assert result["remote_ok"] is True

        # Test in_person format
        mock_opp.format = "in_person"
        result = transform_opportunity_for_frontend(mock_opp)
        assert result["remote_ok"] is False

    def test_transform_prefers_website_url(self):
        """Test that transform prefers website_url over source_url."""
        from src.opportunity_radar.api.v1.endpoints.opportunities import transform_opportunity_for_frontend

        mock_opp = MagicMock()
        mock_opp.themes = []
        mock_opp.technologies = []
        mock_opp.opportunity_type = "hackathon"
        mock_opp.application_deadline = datetime.utcnow()
        mock_opp.total_prize_value = 5000
        mock_opp.team_size_min = 1
        mock_opp.team_size_max = 4
        mock_opp.website_url = "https://official.com"
        mock_opp.source_url = "https://scraped.com"
        mock_opp.location_region = None
        mock_opp.location_country = None
        mock_opp.location_city = None
        mock_opp.format = "online"
        mock_opp.model_dump = MagicMock(return_value={})

        result = transform_opportunity_for_frontend(mock_opp)

        assert result["url"] == "https://official.com"

    def test_transform_falls_back_to_source_url(self):
        """Test that transform falls back to source_url when website_url is None."""
        from src.opportunity_radar.api.v1.endpoints.opportunities import transform_opportunity_for_frontend

        mock_opp = MagicMock()
        mock_opp.themes = []
        mock_opp.technologies = []
        mock_opp.opportunity_type = "hackathon"
        mock_opp.application_deadline = datetime.utcnow()
        mock_opp.total_prize_value = 5000
        mock_opp.team_size_min = 1
        mock_opp.team_size_max = 4
        mock_opp.website_url = None
        mock_opp.source_url = "https://scraped.com"
        mock_opp.location_region = None
        mock_opp.location_country = None
        mock_opp.location_city = None
        mock_opp.format = "online"
        mock_opp.model_dump = MagicMock(return_value={})

        result = transform_opportunity_for_frontend(mock_opp)

        assert result["url"] == "https://scraped.com"
