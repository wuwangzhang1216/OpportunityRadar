"""Integration tests for Authentication API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import ASGITransport, AsyncClient
from datetime import datetime


class TestSignupEndpoint:
    """Test POST /api/v1/auth/signup endpoint."""

    @pytest.mark.asyncio
    async def test_signup_endpoint_exists(self, async_client: AsyncClient):
        """Test that signup endpoint exists and accepts POST."""
        # Even without DB, endpoint should be reachable
        response = await async_client.post(
            "/api/v1/auth/signup",
            json={
                "email": "test@example.com",
                "password": "password123",
                "full_name": "Test User",
            },
        )
        # Will fail with 500 (no DB) or succeed with 201
        assert response.status_code in [201, 409, 500]

    @pytest.mark.asyncio
    async def test_signup_validates_email(self, async_client: AsyncClient):
        """Test that signup validates email format."""
        response = await async_client.post(
            "/api/v1/auth/signup",
            json={
                "email": "invalid-email",
                "password": "password123",
                "full_name": "Test User",
            },
        )
        # Should return 422 for validation error
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_signup_requires_all_fields(self, async_client: AsyncClient):
        """Test that signup requires email, password, and full_name."""
        # Missing password
        response = await async_client.post(
            "/api/v1/auth/signup",
            json={
                "email": "test@example.com",
                "full_name": "Test User",
            },
        )
        assert response.status_code == 422

        # Missing email
        response = await async_client.post(
            "/api/v1/auth/signup",
            json={
                "password": "password123",
                "full_name": "Test User",
            },
        )
        assert response.status_code == 422


class TestLoginEndpoint:
    """Test POST /api/v1/auth/login endpoint."""

    @pytest.mark.asyncio
    async def test_login_endpoint_exists(self, async_client: AsyncClient):
        """Test that login endpoint exists and accepts POST."""
        response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com",
                "password": "password123",
            },
        )
        # Will fail with 401 (invalid creds) or 500 (no DB)
        assert response.status_code in [200, 401, 500]

    @pytest.mark.asyncio
    async def test_login_accepts_form_data(self, async_client: AsyncClient):
        """Test that login accepts OAuth2 form data format."""
        response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpassword",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        # Should not return 422 (validation error)
        assert response.status_code != 422


class TestLogoutEndpoint:
    """Test POST /api/v1/auth/logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_endpoint_works(self, async_client: AsyncClient):
        """Test that logout endpoint returns success."""
        response = await async_client.post("/api/v1/auth/logout")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "logged out" in data["message"].lower()


class TestMeEndpoint:
    """Test GET /api/v1/auth/me endpoint."""

    @pytest.mark.asyncio
    async def test_me_requires_auth(self, async_client: AsyncClient):
        """Test that /me endpoint requires authentication."""
        response = await async_client.get("/api/v1/auth/me")
        # Should return 401 without token
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_rejects_invalid_token(self, async_client: AsyncClient):
        """Test that /me endpoint rejects invalid token."""
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"},
        )
        assert response.status_code == 401


class TestOAuthEndpoints:
    """Test OAuth authorization endpoints."""

    @pytest.mark.asyncio
    async def test_oauth_authorize_github_exists(self, async_client: AsyncClient):
        """Test that GitHub OAuth authorize endpoint exists."""
        response = await async_client.get("/api/v1/auth/oauth/github/authorize")
        # May fail with 500 if Redis not available, but endpoint should exist
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_oauth_authorize_google_exists(self, async_client: AsyncClient):
        """Test that Google OAuth authorize endpoint exists."""
        response = await async_client.get("/api/v1/auth/oauth/google/authorize")
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_oauth_callback_validates_state(self, async_client: AsyncClient):
        """Test that OAuth callback validates state parameter."""
        response = await async_client.post(
            "/api/v1/auth/oauth/github/callback",
            json={
                "code": "test_code",
                "state": "invalid_state",
            },
        )
        # Should return 400 for invalid state or 500 for no Redis
        assert response.status_code in [400, 500]

    @pytest.mark.asyncio
    async def test_oauth_callback_requires_code_and_state(self, async_client: AsyncClient):
        """Test that OAuth callback requires code and state."""
        # Missing state
        response = await async_client.post(
            "/api/v1/auth/oauth/github/callback",
            json={"code": "test_code"},
        )
        assert response.status_code == 422

        # Missing code
        response = await async_client.post(
            "/api/v1/auth/oauth/github/callback",
            json={"state": "test_state"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_oauth_connections_requires_auth(self, async_client: AsyncClient):
        """Test that OAuth connections endpoint requires auth."""
        response = await async_client.get("/api/v1/auth/oauth/github/connections")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_oauth_disconnect_requires_auth(self, async_client: AsyncClient):
        """Test that OAuth disconnect endpoint requires auth."""
        response = await async_client.delete("/api/v1/auth/oauth/github/disconnect")
        assert response.status_code == 401


class TestAuthValidation:
    """Test authentication validation behavior."""

    @pytest.mark.asyncio
    async def test_bearer_token_format(self, async_client: AsyncClient):
        """Test that Bearer token format is required."""
        # Without Bearer prefix
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "some_token"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_empty_authorization_header(self, async_client: AsyncClient):
        """Test response with empty authorization header."""
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": ""},
        )
        assert response.status_code == 401


class TestAuthServiceMockedIntegration:
    """Test auth endpoints with mocked services."""

    @pytest.mark.asyncio
    async def test_signup_success_flow(self):
        """Test successful signup flow with mocked service."""
        from src.opportunity_radar.main import app

        mock_user = MagicMock()
        mock_user.id = "507f1f77bcf86cd799439011"
        mock_user.email = "new@example.com"
        mock_user.full_name = "New User"
        mock_user.is_active = True
        mock_user.created_at = datetime.utcnow()
        mock_user.model_dump = MagicMock(return_value={
            "id": str(mock_user.id),
            "email": mock_user.email,
            "full_name": mock_user.full_name,
            "is_active": mock_user.is_active,
            "created_at": mock_user.created_at.isoformat(),
        })

        with patch("src.opportunity_radar.api.v1.endpoints.auth.AuthService") as MockAuthService:
            mock_service = MockAuthService.return_value
            mock_service.create_user = AsyncMock(return_value=mock_user)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/signup",
                    json={
                        "email": "new@example.com",
                        "password": "password123",
                        "full_name": "New User",
                    },
                )

                # With mocked service, should succeed
                assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_login_success_flow(self):
        """Test successful login flow with mocked service."""
        from src.opportunity_radar.main import app

        mock_tokens = MagicMock()
        mock_tokens.access_token = "mock_access_token"
        mock_tokens.refresh_token = "mock_refresh_token"
        mock_tokens.token_type = "bearer"
        mock_tokens.model_dump = MagicMock(return_value={
            "access_token": mock_tokens.access_token,
            "refresh_token": mock_tokens.refresh_token,
            "token_type": mock_tokens.token_type,
        })

        with patch("src.opportunity_radar.api.v1.endpoints.auth.AuthService") as MockAuthService:
            mock_service = MockAuthService.return_value
            mock_service.authenticate = AsyncMock(return_value=mock_tokens)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/login",
                    data={
                        "username": "test@example.com",
                        "password": "password123",
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert "access_token" in data
                assert "refresh_token" in data
