"""Unit tests for Authentication workflow."""

import pytest


class TestAuthServiceImport:
    """Test AuthService import and structure."""

    def test_import_auth_service(self):
        """Test AuthService import."""
        from src.opportunity_radar.services.auth_service import AuthService

        assert AuthService is not None

    def test_auth_service_has_create_user(self):
        """Test AuthService has create_user method."""
        from src.opportunity_radar.services.auth_service import AuthService

        assert hasattr(AuthService, "create_user")

    def test_auth_service_has_authenticate(self):
        """Test AuthService has authenticate method."""
        from src.opportunity_radar.services.auth_service import AuthService

        assert hasattr(AuthService, "authenticate")

    def test_auth_service_has_get_current_user(self):
        """Test AuthService has get_current_user method."""
        from src.opportunity_radar.services.auth_service import AuthService

        assert hasattr(AuthService, "get_current_user")

    def test_auth_service_has_get_user_by_id(self):
        """Test AuthService has get_user_by_id method."""
        from src.opportunity_radar.services.auth_service import AuthService

        assert hasattr(AuthService, "get_user_by_id")


class TestSecurityModule:
    """Test security module functions."""

    def test_import_create_access_token(self):
        """Test create_access_token import."""
        from src.opportunity_radar.core.security import create_access_token

        assert create_access_token is not None
        assert callable(create_access_token)

    def test_import_create_refresh_token(self):
        """Test create_refresh_token import."""
        from src.opportunity_radar.core.security import create_refresh_token

        assert create_refresh_token is not None
        assert callable(create_refresh_token)

    def test_import_decode_token(self):
        """Test decode_token import."""
        from src.opportunity_radar.core.security import decode_token

        assert decode_token is not None
        assert callable(decode_token)

    def test_import_get_password_hash(self):
        """Test get_password_hash import."""
        from src.opportunity_radar.core.security import get_password_hash

        assert get_password_hash is not None
        assert callable(get_password_hash)

    def test_import_verify_password(self):
        """Test verify_password import."""
        from src.opportunity_radar.core.security import verify_password

        assert verify_password is not None
        assert callable(verify_password)


class TestPasswordHashing:
    """Test password hashing functionality."""

    def test_password_hash_generation(self):
        """Test password hash is generated."""
        from src.opportunity_radar.core.security import get_password_hash

        password = "test_password_123"
        hashed = get_password_hash(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 20

    def test_password_verification_correct(self):
        """Test password verification with correct password."""
        from src.opportunity_radar.core.security import (
            get_password_hash,
            verify_password,
        )

        password = "test_password_123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_password_verification_incorrect(self):
        """Test password verification with incorrect password."""
        from src.opportunity_radar.core.security import (
            get_password_hash,
            verify_password,
        )

        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False


class TestTokenGeneration:
    """Test token generation functionality."""

    def test_access_token_generation(self):
        """Test access token is generated."""
        from src.opportunity_radar.core.security import create_access_token

        token = create_access_token(data={"sub": "test_user_id"})

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50

    def test_refresh_token_generation(self):
        """Test refresh token is generated."""
        from src.opportunity_radar.core.security import create_refresh_token

        token = create_refresh_token(data={"sub": "test_user_id"})

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50

    def test_tokens_are_different(self):
        """Test access and refresh tokens are different."""
        from src.opportunity_radar.core.security import (
            create_access_token,
            create_refresh_token,
        )

        access = create_access_token(data={"sub": "test_user_id"})
        refresh = create_refresh_token(data={"sub": "test_user_id"})

        assert access != refresh


class TestUserModel:
    """Test User model for auth."""

    def test_import_user(self):
        """Test User model import."""
        from src.opportunity_radar.models import User

        assert User is not None

    def test_user_has_auth_fields(self):
        """Test User has authentication-related fields."""
        from src.opportunity_radar.models.user import User

        fields = User.model_fields

        assert "email" in fields
        assert "hashed_password" in fields
        assert "is_active" in fields

    def test_user_has_profile_fields(self):
        """Test User has profile-related fields."""
        from src.opportunity_radar.models.user import User

        fields = User.model_fields

        assert "full_name" in fields
        assert "created_at" in fields


class TestAuthSchemas:
    """Test authentication schemas."""

    def test_import_token_schema(self):
        """Test Token schema import."""
        from src.opportunity_radar.schemas.user import Token

        assert Token is not None

    def test_import_user_create_schema(self):
        """Test UserCreate schema import."""
        from src.opportunity_radar.schemas.user import UserCreate

        assert UserCreate is not None

    def test_import_user_response_schema(self):
        """Test UserResponse schema import."""
        from src.opportunity_radar.schemas.user import UserResponse

        assert UserResponse is not None

    def test_token_schema_fields(self):
        """Test Token schema has required fields."""
        from src.opportunity_radar.schemas.user import Token

        fields = Token.model_fields

        assert "access_token" in fields
        assert "refresh_token" in fields
        assert "token_type" in fields
