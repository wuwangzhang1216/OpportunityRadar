"""OAuth providers for GitHub and Google authentication."""

import logging
from typing import Dict, Optional
from dataclasses import dataclass

import httpx

from ..config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class OAuthUser:
    """OAuth user data from provider."""

    provider: str
    provider_id: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    access_token: Optional[str] = None


class GitHubOAuth:
    """GitHub OAuth provider."""

    AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USER_URL = "https://api.github.com/user"
    EMAILS_URL = "https://api.github.com/user/emails"

    def __init__(self):
        settings = get_settings()
        self.client_id = settings.github_client_id
        self.client_secret = settings.github_client_secret
        self.redirect_uri = settings.github_redirect_uri

    def get_authorize_url(self, state: str) -> str:
        """Get the GitHub authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "user:email read:user",
            "state": state,
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTHORIZE_URL}?{query}"

    async def exchange_code(self, code: str) -> Optional[str]:
        """Exchange authorization code for access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                },
                headers={"Accept": "application/json"},
            )

            if response.status_code != 200:
                logger.error(f"GitHub token exchange failed: {response.text}")
                return None

            data = response.json()
            return data.get("access_token")

    async def get_user_info(self, access_token: str) -> Optional[OAuthUser]:
        """Get user information from GitHub."""
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            }

            # Get user profile
            response = await client.get(self.USER_URL, headers=headers)
            if response.status_code != 200:
                logger.error(f"GitHub user info failed: {response.text}")
                return None

            user_data = response.json()

            # Get email if not public
            email = user_data.get("email")
            if not email:
                emails_response = await client.get(self.EMAILS_URL, headers=headers)
                if emails_response.status_code == 200:
                    emails = emails_response.json()
                    primary = next((e for e in emails if e.get("primary")), None)
                    if primary:
                        email = primary.get("email")

            if not email:
                logger.error("Could not get email from GitHub")
                return None

            return OAuthUser(
                provider="github",
                provider_id=str(user_data["id"]),
                email=email,
                name=user_data.get("name") or user_data.get("login"),
                avatar_url=user_data.get("avatar_url"),
                access_token=access_token,
            )


class GoogleOAuth:
    """Google OAuth provider."""

    AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USER_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    def __init__(self):
        settings = get_settings()
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.redirect_uri = settings.google_redirect_uri

    def get_authorize_url(self, state: str) -> str:
        """Get the Google authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTHORIZE_URL}?{query}"

    async def exchange_code(self, code: str) -> Optional[str]:
        """Exchange authorization code for access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                    "grant_type": "authorization_code",
                },
            )

            if response.status_code != 200:
                logger.error(f"Google token exchange failed: {response.text}")
                return None

            data = response.json()
            return data.get("access_token")

    async def get_user_info(self, access_token: str) -> Optional[OAuthUser]:
        """Get user information from Google."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.USER_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code != 200:
                logger.error(f"Google user info failed: {response.text}")
                return None

            user_data = response.json()

            email = user_data.get("email")
            if not email:
                logger.error("Could not get email from Google")
                return None

            return OAuthUser(
                provider="google",
                provider_id=user_data["id"],
                email=email,
                name=user_data.get("name"),
                avatar_url=user_data.get("picture"),
                access_token=access_token,
            )


def get_oauth_provider(provider: str):
    """Get OAuth provider by name."""
    if provider == "github":
        return GitHubOAuth()
    elif provider == "google":
        return GoogleOAuth()
    else:
        raise ValueError(f"Unknown OAuth provider: {provider}")
