"""User model for MongoDB."""

from datetime import datetime
from typing import List, Optional

from beanie import Document, Indexed
from pydantic import EmailStr, Field


class User(Document):
    """User model for authentication and account management."""

    email: Indexed(EmailStr, unique=True)
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"

    def __repr__(self) -> str:
        return f"<User {self.email}>"
