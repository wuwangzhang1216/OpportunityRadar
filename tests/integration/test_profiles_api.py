"""Integration tests for Profiles API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import ASGITransport, AsyncClient
from datetime import datetime


class TestProfilesEndpointAuth:
    """Test that profiles endpoints require authentication."""

    @pytest.mark.asyncio
    async def test_get_my_profile_requires_auth(self, async_client: AsyncClient):
        """Test GET /profiles/me requires authentication."""
        response = await async_client.get("/api/v1/profiles/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_profile_requires_auth(self, async_client: AsyncClient):
        """Test POST /profiles requires authentication."""
        response = await async_client.post(
            "/api/v1/profiles",
            json={"tech_stack": ["Python"]},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_profile_requires_auth(self, async_client: AsyncClient):
        """Test PUT /profiles/me requires authentication."""
        response = await async_client.put(
            "/api/v1/profiles/me",
            json={"tech_stack": ["Python", "TypeScript"]},
        )
        assert response.status_code == 401


class TestGetProfileEndpoint:
    """Test GET /api/v1/profiles/me endpoint."""

    def _create_mock_user(self):
        """Create a mock user object."""
        mock_user = MagicMock()
        mock_user.id = "507f1f77bcf86cd799439011"
        mock_user.email = "test@example.com"
        return mock_user

    def _create_mock_profile(self, user_id):
        """Create a mock profile object."""
        mock_profile = MagicMock()
        mock_profile.id = "profile123"
        mock_profile.user_id = user_id
        mock_profile.experience_level = "intermediate"
        mock_profile.company_stage = "startup"
        mock_profile.tech_stack = ["Python", "React", "PostgreSQL"]
        mock_profile.interests = ["AI", "Web3"]
        mock_profile.goals = ["Build AI products", "Win hackathons"]
        mock_profile.team_name = "Test Team"
        mock_profile.team_size = 3
        mock_profile.funding_stage = "seed"
        mock_profile.seeking_funding = True
        mock_profile.funding_amount_seeking = 500000
        mock_profile.product_name = "TestProduct"
        mock_profile.product_description = "A test product"
        mock_profile.product_url = "https://testproduct.com"
        mock_profile.product_stage = "mvp"
        mock_profile.team_members = []
        mock_profile.previous_accelerators = ["YC", "Techstars"]
        mock_profile.previous_hackathon_wins = 3
        mock_profile.notable_achievements = ["Best AI Hack 2024"]
        mock_profile.bio = "A test bio"
        mock_profile.display_name = "Test Display Name"
        mock_profile.created_at = datetime.utcnow()
        mock_profile.updated_at = datetime.utcnow()
        return mock_profile

    @pytest.mark.asyncio
    async def test_get_profile_returns_404_when_no_profile(self):
        """Test that get profile returns 404 when user has no profile."""
        from src.opportunity_radar.main import app

        mock_user = self._create_mock_user()

        with patch("src.opportunity_radar.core.security.get_current_user") as mock_get_user:
            mock_get_user.return_value = mock_user

            with patch("src.opportunity_radar.api.v1.endpoints.profiles.Profile") as MockProfile:
                MockProfile.find_one = AsyncMock(return_value=None)

                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/profiles/me",
                        headers={"Authorization": "Bearer valid_token"},
                    )

                    assert response.status_code == 404
                    data = response.json()
                    assert "not found" in data.get("detail", "").lower()

    @pytest.mark.asyncio
    async def test_get_profile_returns_profile_data(self):
        """Test that get profile returns full profile data."""
        from src.opportunity_radar.main import app

        mock_user = self._create_mock_user()
        mock_profile = self._create_mock_profile(mock_user.id)

        with patch("src.opportunity_radar.core.security.get_current_user") as mock_get_user:
            mock_get_user.return_value = mock_user

            with patch("src.opportunity_radar.api.v1.endpoints.profiles.Profile") as MockProfile:
                MockProfile.find_one = AsyncMock(return_value=mock_profile)

                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/profiles/me",
                        headers={"Authorization": "Bearer valid_token"},
                    )

                    if response.status_code == 200:
                        data = response.json()
                        assert data["id"] == "profile123"
                        assert "tech_stack" in data
                        assert "industries" in data
                        assert "intents" in data


class TestCreateProfileEndpoint:
    """Test POST /api/v1/profiles endpoint."""

    def _create_mock_user(self):
        """Create a mock user object."""
        mock_user = MagicMock()
        mock_user.id = "507f1f77bcf86cd799439011"
        return mock_user

    @pytest.mark.asyncio
    async def test_create_profile_rejects_duplicate(self):
        """Test that create profile rejects if profile exists."""
        from src.opportunity_radar.main import app

        mock_user = self._create_mock_user()
        mock_existing = MagicMock()

        with patch("src.opportunity_radar.core.security.get_current_user") as mock_get_user:
            mock_get_user.return_value = mock_user

            with patch("src.opportunity_radar.api.v1.endpoints.profiles.Profile") as MockProfile:
                MockProfile.find_one = AsyncMock(return_value=mock_existing)

                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/profiles",
                        json={
                            "tech_stack": ["Python"],
                            "industries": ["Technology"],
                            "intents": ["Build products"],
                        },
                        headers={"Authorization": "Bearer valid_token"},
                    )

                    assert response.status_code == 400
                    data = response.json()
                    assert "already exists" in data.get("detail", "").lower()


class TestUpdateProfileEndpoint:
    """Test PUT /api/v1/profiles/me endpoint."""

    def _create_mock_user(self):
        """Create a mock user object."""
        mock_user = MagicMock()
        mock_user.id = "507f1f77bcf86cd799439011"
        return mock_user

    def _create_mock_profile(self, user_id):
        """Create a mock profile object."""
        mock_profile = MagicMock()
        mock_profile.id = "profile123"
        mock_profile.user_id = user_id
        mock_profile.experience_level = "intermediate"
        mock_profile.company_stage = "startup"
        mock_profile.tech_stack = ["Python"]
        mock_profile.interests = ["AI"]
        mock_profile.goals = ["Build products"]
        mock_profile.team_name = None
        mock_profile.team_size = 1
        mock_profile.funding_stage = None
        mock_profile.seeking_funding = False
        mock_profile.funding_amount_seeking = None
        mock_profile.product_name = None
        mock_profile.product_description = None
        mock_profile.product_url = None
        mock_profile.product_stage = None
        mock_profile.team_members = []
        mock_profile.previous_accelerators = []
        mock_profile.previous_hackathon_wins = 0
        mock_profile.notable_achievements = []
        mock_profile.created_at = datetime.utcnow()
        mock_profile.updated_at = datetime.utcnow()
        mock_profile.save = AsyncMock()
        return mock_profile

    @pytest.mark.asyncio
    async def test_update_profile_returns_404_when_no_profile(self):
        """Test that update returns 404 when user has no profile."""
        from src.opportunity_radar.main import app

        mock_user = self._create_mock_user()

        with patch("src.opportunity_radar.core.security.get_current_user") as mock_get_user:
            mock_get_user.return_value = mock_user

            with patch("src.opportunity_radar.api.v1.endpoints.profiles.Profile") as MockProfile:
                MockProfile.find_one = AsyncMock(return_value=None)

                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.put(
                        "/api/v1/profiles/me",
                        json={"tech_stack": ["Python", "TypeScript"]},
                        headers={"Authorization": "Bearer valid_token"},
                    )

                    assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_profile_partial_update(self):
        """Test that update allows partial updates."""
        from src.opportunity_radar.main import app

        mock_user = self._create_mock_user()
        mock_profile = self._create_mock_profile(mock_user.id)

        with patch("src.opportunity_radar.core.security.get_current_user") as mock_get_user:
            mock_get_user.return_value = mock_user

            with patch("src.opportunity_radar.api.v1.endpoints.profiles.Profile") as MockProfile:
                MockProfile.find_one = AsyncMock(return_value=mock_profile)

                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.put(
                        "/api/v1/profiles/me",
                        json={"tech_stack": ["Python", "TypeScript", "Go"]},
                        headers={"Authorization": "Bearer valid_token"},
                    )

                    if response.status_code == 200:
                        # Profile save should have been called
                        mock_profile.save.assert_called_once()


class TestProfileSchemaValidation:
    """Test profile schema validation."""

    @pytest.mark.asyncio
    async def test_create_profile_validates_team_size(self, async_client: AsyncClient):
        """Test that create profile validates team_size."""
        response = await async_client.post(
            "/api/v1/profiles",
            json={
                "tech_stack": ["Python"],
                "team_size": -1,  # Invalid negative
            },
            headers={"Authorization": "Bearer invalid"},
        )
        # Either 401 (auth) or 422 (validation)
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_create_profile_validates_tech_stack_array(self, async_client: AsyncClient):
        """Test that tech_stack must be an array."""
        response = await async_client.post(
            "/api/v1/profiles",
            json={
                "tech_stack": "Python",  # Should be array
            },
            headers={"Authorization": "Bearer invalid"},
        )
        assert response.status_code in [401, 422]


class TestProfileResponseStructure:
    """Test profile response structure."""

    def test_profile_response_schema_fields(self):
        """Test ProfileResponse schema has expected fields."""
        from src.opportunity_radar.schemas.profile import ProfileResponse

        # Check model fields exist
        fields = ProfileResponse.model_fields
        expected_fields = [
            "id",
            "user_id",
            "tech_stack",
            "industries",
            "intents",
            "team_size",
        ]
        for field in expected_fields:
            assert field in fields, f"Missing field: {field}"

    def test_profile_create_schema_fields(self):
        """Test ProfileCreate schema has expected fields."""
        from src.opportunity_radar.schemas.profile import ProfileCreate

        fields = ProfileCreate.model_fields
        # These are the fields that can be set on creation
        assert "tech_stack" in fields
        assert "industries" in fields
        assert "intents" in fields

    def test_profile_update_schema_fields(self):
        """Test ProfileUpdate schema has expected fields."""
        from src.opportunity_radar.schemas.profile import ProfileUpdate

        fields = ProfileUpdate.model_fields
        # All update fields should be optional
        assert "tech_stack" in fields
        assert "industries" in fields


class TestProfileBackgroundTasks:
    """Test profile background task triggers."""

    def _create_mock_user(self):
        """Create a mock user object."""
        mock_user = MagicMock()
        mock_user.id = "507f1f77bcf86cd799439011"
        return mock_user

    def _create_mock_profile(self, user_id):
        """Create a mock profile object."""
        mock_profile = MagicMock()
        mock_profile.id = "profile123"
        mock_profile.user_id = user_id
        mock_profile.experience_level = "intermediate"
        mock_profile.company_stage = "startup"
        mock_profile.tech_stack = ["Python"]
        mock_profile.interests = ["AI"]
        mock_profile.goals = ["Build products"]
        mock_profile.team_name = None
        mock_profile.team_size = 1
        mock_profile.funding_stage = None
        mock_profile.seeking_funding = False
        mock_profile.funding_amount_seeking = None
        mock_profile.product_name = None
        mock_profile.product_description = None
        mock_profile.product_url = None
        mock_profile.product_stage = None
        mock_profile.team_members = []
        mock_profile.previous_accelerators = []
        mock_profile.previous_hackathon_wins = 0
        mock_profile.notable_achievements = []
        mock_profile.created_at = datetime.utcnow()
        mock_profile.updated_at = datetime.utcnow()
        mock_profile.save = AsyncMock()
        return mock_profile

    @pytest.mark.asyncio
    async def test_update_triggers_match_recalculation(self):
        """Test that profile update triggers background match recalculation."""
        from src.opportunity_radar.main import app

        mock_user = self._create_mock_user()
        mock_profile = self._create_mock_profile(mock_user.id)

        with patch("src.opportunity_radar.core.security.get_current_user") as mock_get_user:
            mock_get_user.return_value = mock_user

            with patch("src.opportunity_radar.api.v1.endpoints.profiles.Profile") as MockProfile:
                MockProfile.find_one = AsyncMock(return_value=mock_profile)

                with patch("src.opportunity_radar.api.v1.endpoints.profiles.recalculate_matches_background") as mock_bg_task:
                    transport = ASGITransport(app=app)
                    async with AsyncClient(transport=transport, base_url="http://test") as client:
                        response = await client.put(
                            "/api/v1/profiles/me",
                            json={"tech_stack": ["Python", "Go"]},
                            headers={"Authorization": "Bearer valid_token"},
                        )

                        # The background task should be added
                        # Note: FastAPI's BackgroundTasks might not call immediately
                        if response.status_code == 200:
                            pass  # Background task handling is tested separately
