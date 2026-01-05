"""Authentication endpoints."""

import secrets
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from ....schemas.user import UserCreate, UserResponse, Token
from ....services.auth_service import AuthService
from ....core.oauth import get_oauth_provider, OAuthUser
from ....models.user import User

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# In-memory state storage (use Redis in production)
_oauth_states: dict = {}


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request."""

    code: str
    state: str


class OAuthURLResponse(BaseModel):
    """OAuth authorization URL response."""

    url: str
    state: str


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate):
    """Register a new user."""
    auth_service = AuthService()
    user = await auth_service.create_user(user_data)
    return user


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return JWT tokens."""
    auth_service = AuthService()
    tokens = await auth_service.authenticate(form_data.username, form_data.password)
    return tokens


@router.post("/logout")
async def logout():
    """Logout user (client should discard tokens)."""
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current authenticated user."""
    auth_service = AuthService()
    user = await auth_service.get_current_user(token)
    return user


@router.get("/oauth/{provider}/authorize", response_model=OAuthURLResponse)
async def oauth_authorize(
    provider: Literal["github", "google"],
):
    """Get OAuth authorization URL for a provider."""
    oauth = get_oauth_provider(provider)

    # Generate and store state for CSRF protection
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = {
        "provider": provider,
        "created_at": datetime.utcnow(),
    }

    url = oauth.get_authorize_url(state)

    return OAuthURLResponse(url=url, state=state)


@router.post("/oauth/{provider}/callback", response_model=Token)
async def oauth_callback(
    provider: Literal["github", "google"],
    callback: OAuthCallbackRequest,
):
    """Handle OAuth callback and exchange code for tokens."""
    # Validate state
    if callback.state not in _oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state parameter",
        )

    state_data = _oauth_states.pop(callback.state)
    if state_data["provider"] != provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider mismatch",
        )

    # Exchange code for access token
    oauth = get_oauth_provider(provider)
    access_token = await oauth.exchange_code(callback.code)

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange authorization code",
        )

    # Get user info
    oauth_user = await oauth.get_user_info(access_token)
    if not oauth_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user information from provider",
        )

    # Find or create user
    auth_service = AuthService()
    user = await User.find_one(User.email == oauth_user.email)

    if user:
        # Update OAuth connection
        user.add_oauth_connection(
            provider=oauth_user.provider,
            provider_id=oauth_user.provider_id,
            access_token=access_token,
        )
        if oauth_user.avatar_url and not user.avatar_url:
            user.avatar_url = oauth_user.avatar_url
        if oauth_user.name and not user.full_name:
            user.full_name = oauth_user.name
        user.last_login_at = datetime.utcnow()
        await user.save()
    else:
        # Create new user
        user = User(
            email=oauth_user.email,
            full_name=oauth_user.name,
            avatar_url=oauth_user.avatar_url,
            hashed_password=None,  # OAuth users don't have password
        )
        user.add_oauth_connection(
            provider=oauth_user.provider,
            provider_id=oauth_user.provider_id,
            access_token=access_token,
        )
        user.last_login_at = datetime.utcnow()
        await user.insert()

    # Generate JWT tokens
    tokens = auth_service.create_tokens(str(user.id))

    return tokens


@router.get("/oauth/{provider}/connections")
async def get_oauth_connections(
    token: str = Depends(oauth2_scheme),
):
    """Get connected OAuth providers for current user."""
    auth_service = AuthService()
    user = await auth_service.get_current_user(token)

    return {
        "connections": [
            {
                "provider": conn.provider,
                "connected_at": conn.connected_at.isoformat(),
            }
            for conn in user.oauth_connections
        ]
    }


@router.delete("/oauth/{provider}/disconnect")
async def disconnect_oauth(
    provider: Literal["github", "google"],
    token: str = Depends(oauth2_scheme),
):
    """Disconnect an OAuth provider from current user."""
    auth_service = AuthService()
    user = await auth_service.get_current_user(token)

    # Ensure user has a password or other OAuth connection
    if not user.hashed_password and len(user.oauth_connections) <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot disconnect the only authentication method. Set a password first.",
        )

    # Remove OAuth connection
    user.oauth_connections = [
        c for c in user.oauth_connections if c.provider != provider
    ]
    user.updated_at = datetime.utcnow()
    await user.save()

    return {"message": f"Disconnected {provider}"}
