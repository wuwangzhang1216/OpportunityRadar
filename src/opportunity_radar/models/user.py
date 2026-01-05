"""User model for MongoDB."""

from datetime import datetime, timezone
from typing import List, Literal, Optional

from beanie import Document, Indexed
from pydantic import BaseModel, EmailStr, Field


def _utc_now() -> datetime:
    """Return current UTC time with timezone info."""
    return datetime.now(timezone.utc)


OAuthProvider = Literal["github", "google"]


class OAuthConnection(BaseModel):
    """OAuth provider connection."""

    provider: OAuthProvider
    provider_id: str
    connected_at: datetime = Field(default_factory=_utc_now)
    access_token: Optional[str] = None  # Encrypted in production


class User(Document):
    """User model for authentication and account management."""

    email: Indexed(EmailStr, unique=True)
    hashed_password: Optional[str] = None  # Can be null for OAuth-only users
    full_name: str | None = None
    avatar_url: str | None = None
    is_active: bool = True
    is_superuser: bool = False

    # OAuth connections
    oauth_connections: List[OAuthConnection] = Field(default_factory=list)

    # Timestamps
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)
    last_login_at: Optional[datetime] = None

    class Settings:
        name = "users"

    def __repr__(self) -> str:
        return f"<User {self.email}>"

    def has_oauth_provider(self, provider: str) -> bool:
        """Check if user has a specific OAuth provider connected."""
        return any(conn.provider == provider for conn in self.oauth_connections)

    def get_oauth_connection(self, provider: str) -> Optional[OAuthConnection]:
        """Get OAuth connection by provider."""
        for conn in self.oauth_connections:
            if conn.provider == provider:
                return conn
        return None

    def add_oauth_connection(
        self,
        provider: str,
        provider_id: str,
        access_token: Optional[str] = None,
    ) -> None:
        """Add or update OAuth connection."""
        # Remove existing connection for this provider
        self.oauth_connections = [
            c for c in self.oauth_connections if c.provider != provider
        ]

        # Add new connection
        self.oauth_connections.append(
            OAuthConnection(
                provider=provider,
                provider_id=provider_id,
                access_token=access_token,
            )
        )
        self.updated_at = _utc_now()
