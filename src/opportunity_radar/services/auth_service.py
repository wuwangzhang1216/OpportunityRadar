"""Authentication service for MongoDB."""

from beanie import PydanticObjectId

from ..core.exceptions import ConflictException, UnauthorizedException
from ..core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from ..models.user import User
from ..models.profile import Profile
from ..schemas.user import Token, UserCreate, UserResponse


class AuthService:
    """Service for authentication operations."""

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user."""
        # Check if user already exists
        existing = await User.find_one(User.email == user_data.email)
        if existing:
            raise ConflictException(message="User with this email already exists")

        # Create new user
        user = User(
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
        )
        await user.insert()

        return UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
        )

    async def authenticate(self, email: str, password: str) -> Token:
        """Authenticate user and return tokens."""
        # Find user
        user = await User.find_one(User.email == email)

        if not user:
            raise UnauthorizedException(message="Invalid email or password")

        if not verify_password(password, user.hashed_password):
            raise UnauthorizedException(message="Invalid email or password")

        if not user.is_active:
            raise UnauthorizedException(message="User account is disabled")

        # Create tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def get_current_user(self, token: str) -> UserResponse:
        """Get current user from token."""
        payload = decode_token(token)
        if not payload:
            raise UnauthorizedException(message="Invalid or expired token")

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException(message="Invalid token payload")

        user = await User.get(PydanticObjectId(user_id))

        if not user:
            raise UnauthorizedException(message="User not found")

        if not user.is_active:
            raise UnauthorizedException(message="User account is disabled")

        # Check if user has profile
        profile = await Profile.find_one(Profile.user_id == user.id)
        has_profile = profile is not None

        return UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            has_profile=has_profile,
            created_at=user.created_at,
        )

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Get user by ID."""
        return await User.get(PydanticObjectId(user_id))
