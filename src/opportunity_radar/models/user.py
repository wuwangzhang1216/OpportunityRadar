"""User model for MongoDB."""

from datetime import datetime, timezone
from typing import Optional

from beanie import Document, Indexed
from pydantic import EmailStr, Field


def _utc_now() -> datetime:
    """Return current UTC time with timezone info."""
    return datetime.now(timezone.utc)


class User(Document):
    """User model for authentication and account management."""

    email: Indexed(EmailStr, unique=True)
    hashed_password: str
    full_name: str | None = None
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)

    class Settings:
        name = "users"

    def __repr__(self) -> str:
        return f"<User {self.email}>"
