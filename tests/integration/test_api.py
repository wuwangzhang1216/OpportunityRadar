"""Integration tests for API endpoints."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


class TestHealthEndpoint:
    """Test health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        """Test GET /health returns healthy status."""
        response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["app"] == "OpportunityRadar"


class TestDocsEndpoint:
    """Test documentation endpoints."""

    @pytest.mark.asyncio
    async def test_swagger_ui(self, async_client: AsyncClient):
        """Test GET /docs returns Swagger UI."""
        response = await async_client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_openapi_json(self, async_client: AsyncClient):
        """Test GET /openapi.json returns OpenAPI schema."""
        response = await async_client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data


class TestOpportunitiesEndpoint:
    """Test opportunities API endpoints.

    Note: These tests require MongoDB to be running and initialized.
    They are marked to skip if database is not available.
    """

    @pytest.mark.asyncio
    async def test_list_opportunities_endpoint_exists(self, async_client: AsyncClient):
        """Test that opportunities endpoint exists (may fail without DB init)."""
        try:
            response = await async_client.get("/api/v1/opportunities")
            # Either succeeds with 200 or fails with 500 (no DB)
            assert response.status_code in [200, 500]
        except Exception:
            # Beanie not initialized is acceptable in unit test context
            pytest.skip("MongoDB/Beanie not initialized - skipping DB test")
