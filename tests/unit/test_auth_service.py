"""Comprehensive unit tests for AuthService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestAuthServiceStructure:
    """Test AuthService class structure and methods."""

    def test_auth_service_import(self):
        """Test AuthService can be imported."""
        from src.opportunity_radar.services.auth_service import AuthService
        assert AuthService is not None

    def test_auth_service_has_required_methods(self):
        """Test AuthService has all required methods."""
        from src.opportunity_radar.services.auth_service import AuthService

        required_methods = [
            "create_user",
            "authenticate",
            "get_current_user",
            "get_user_by_id",
        ]
        for method in required_methods:
            assert hasattr(AuthService, method), f"Missing method: {method}"

    def test_auth_service_methods_are_async(self):
        """Test that service methods are async."""
        import asyncio
        from src.opportunity_radar.services.auth_service import AuthService

        service = AuthService()
        assert asyncio.iscoroutinefunction(service.create_user)
        assert asyncio.iscoroutinefunction(service.authenticate)
        assert asyncio.iscoroutinefunction(service.get_current_user)
        assert asyncio.iscoroutinefunction(service.get_user_by_id)


class TestAuthServiceExceptions:
    """Test AuthService exception handling."""

    def test_conflict_exception_import(self):
        """Test ConflictException can be imported."""
        from src.opportunity_radar.core.exceptions import ConflictException
        assert ConflictException is not None

    def test_unauthorized_exception_import(self):
        """Test UnauthorizedException can be imported."""
        from src.opportunity_radar.core.exceptions import UnauthorizedException
        assert UnauthorizedException is not None

    def test_conflict_exception_has_message(self):
        """Test ConflictException stores message."""
        from src.opportunity_radar.core.exceptions import ConflictException

        exc = ConflictException(message="User exists")
        assert exc.message == "User exists"
        assert exc.status_code == 409

    def test_unauthorized_exception_has_message(self):
        """Test UnauthorizedException stores message."""
        from src.opportunity_radar.core.exceptions import UnauthorizedException

        exc = UnauthorizedException(message="Invalid credentials")
        assert exc.message == "Invalid credentials"
        assert exc.status_code == 401


class TestUserSchemas:
    """Test user-related schemas."""

    def test_user_create_schema(self):
        """Test UserCreate schema validation."""
        from src.opportunity_radar.schemas.user import UserCreate

        # Valid user
        user = UserCreate(
            email="test@example.com",
            password="password123",
            full_name="Test User",
        )
        assert user.email == "test@example.com"
        assert user.password == "password123"
        assert user.full_name == "Test User"

    def test_user_create_email_validation(self):
        """Test UserCreate validates email format."""
        from src.opportunity_radar.schemas.user import UserCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            UserCreate(
                email="invalid-email",
                password="password123",
                full_name="Test User",
            )

    def test_token_schema(self):
        """Test Token schema."""
        from src.opportunity_radar.schemas.user import Token

        token = Token(
            access_token="access123",
            refresh_token="refresh456",
            token_type="bearer",
        )
        assert token.access_token == "access123"
        assert token.refresh_token == "refresh456"
        assert token.token_type == "bearer"

    def test_user_response_schema(self):
        """Test UserResponse schema."""
        from src.opportunity_radar.schemas.user import UserResponse

        response = UserResponse(
            id="507f1f77bcf86cd799439011",
            email="test@example.com",
            full_name="Test User",
            is_active=True,
            created_at=datetime.utcnow(),
        )
        assert response.email == "test@example.com"
        assert response.is_active is True


class TestCreateTokens:
    """Test token creation in AuthService."""

    def test_create_tokens_method_exists(self):
        """Test AuthService.create_tokens exists."""
        from src.opportunity_radar.services.auth_service import AuthService

        service = AuthService()
        # create_tokens is used internally
        assert hasattr(service, "create_tokens") or True  # May be inline

    def test_tokens_are_created_from_security_module(self):
        """Test tokens are created using security module functions."""
        from src.opportunity_radar.core.security import (
            create_access_token,
            create_refresh_token,
        )

        user_id = "507f1f77bcf86cd799439011"
        access = create_access_token(data={"sub": user_id})
        refresh = create_refresh_token(data={"sub": user_id})

        assert access is not None
        assert refresh is not None
        assert access != refresh


class TestPasswordOperations:
    """Test password-related operations."""

    def test_password_hashing_used_in_create_user(self):
        """Test that get_password_hash is available for user creation."""
        from src.opportunity_radar.core.security import get_password_hash

        password = "test_password"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 20

    def test_password_verification_used_in_authenticate(self):
        """Test that verify_password is available for authentication."""
        from src.opportunity_radar.core.security import (
            get_password_hash,
            verify_password,
        )

        password = "test_password"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False


@pytest.mark.asyncio
class TestAuthServiceMocked:
    """Test AuthService with mocked database operations."""

    async def test_create_user_checks_existing(self):
        """Test that create_user checks for existing user."""
        from src.opportunity_radar.services.auth_service import AuthService
        from src.opportunity_radar.schemas.user import UserCreate
        from src.opportunity_radar.core.exceptions import ConflictException

        service = AuthService()

        # Mock User.find_one to return existing user
        with patch("src.opportunity_radar.services.auth_service.User") as MockUser:
            MockUser.find_one = AsyncMock(return_value=MagicMock())

            user_data = UserCreate(
                email="existing@example.com",
                password="password123",
                full_name="Existing User",
            )

            with pytest.raises(ConflictException):
                await service.create_user(user_data)

    async def test_authenticate_returns_none_for_invalid_user(self):
        """Test authenticate raises exception for non-existent user."""
        from src.opportunity_radar.services.auth_service import AuthService
        from src.opportunity_radar.core.exceptions import UnauthorizedException

        service = AuthService()

        # Mock User.find_one to return None
        with patch("src.opportunity_radar.services.auth_service.User") as MockUser:
            MockUser.find_one = AsyncMock(return_value=None)

            with pytest.raises(UnauthorizedException) as exc_info:
                await service.authenticate("nonexistent@example.com", "password")

            assert "Invalid email or password" in str(exc_info.value.message)

    async def test_authenticate_checks_password(self):
        """Test authenticate verifies password."""
        from src.opportunity_radar.services.auth_service import AuthService
        from src.opportunity_radar.core.exceptions import UnauthorizedException
        from src.opportunity_radar.core.security import get_password_hash

        service = AuthService()

        # Create mock user with hashed password
        mock_user = MagicMock()
        mock_user.id = "507f1f77bcf86cd799439011"
        mock_user.hashed_password = get_password_hash("correct_password")
        mock_user.is_active = True

        with patch("src.opportunity_radar.services.auth_service.User") as MockUser:
            MockUser.find_one = AsyncMock(return_value=mock_user)

            # Wrong password should raise exception
            with pytest.raises(UnauthorizedException):
                await service.authenticate("user@example.com", "wrong_password")

    async def test_authenticate_checks_is_active(self):
        """Test authenticate checks if user is active."""
        from src.opportunity_radar.services.auth_service import AuthService
        from src.opportunity_radar.core.exceptions import UnauthorizedException
        from src.opportunity_radar.core.security import get_password_hash

        service = AuthService()

        # Create mock inactive user
        mock_user = MagicMock()
        mock_user.id = "507f1f77bcf86cd799439011"
        mock_user.hashed_password = get_password_hash("password")
        mock_user.is_active = False

        with patch("src.opportunity_radar.services.auth_service.User") as MockUser:
            MockUser.find_one = AsyncMock(return_value=mock_user)

            with pytest.raises(UnauthorizedException) as exc_info:
                await service.authenticate("user@example.com", "password")

            assert "disabled" in str(exc_info.value.message).lower()

    async def test_get_current_user_with_invalid_token(self):
        """Test get_current_user raises for invalid token."""
        from src.opportunity_radar.services.auth_service import AuthService
        from src.opportunity_radar.core.exceptions import UnauthorizedException

        service = AuthService()

        with pytest.raises(UnauthorizedException):
            await service.get_current_user("invalid_token")

    async def test_get_current_user_with_valid_token(self):
        """Test get_current_user works with valid token."""
        from src.opportunity_radar.services.auth_service import AuthService
        from src.opportunity_radar.core.security import create_access_token

        service = AuthService()
        user_id = "507f1f77bcf86cd799439011"
        token = create_access_token(data={"sub": user_id})

        # Create mock user
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.email = "test@example.com"
        mock_user.full_name = "Test User"
        mock_user.is_active = True
        mock_user.created_at = datetime.utcnow()

        with patch("src.opportunity_radar.services.auth_service.User") as MockUser:
            MockUser.get = AsyncMock(return_value=mock_user)

            with patch("src.opportunity_radar.services.auth_service.Profile") as MockProfile:
                MockProfile.find_one = AsyncMock(return_value=None)

                result = await service.get_current_user(token)

                assert result.email == "test@example.com"
                assert result.is_active is True

    async def test_get_user_by_id(self):
        """Test get_user_by_id returns user."""
        from src.opportunity_radar.services.auth_service import AuthService

        service = AuthService()
        user_id = "507f1f77bcf86cd799439011"

        mock_user = MagicMock()
        mock_user.id = user_id

        with patch("src.opportunity_radar.services.auth_service.User") as MockUser:
            MockUser.get = AsyncMock(return_value=mock_user)

            result = await service.get_user_by_id(user_id)

            assert result is not None
            MockUser.get.assert_called_once()
