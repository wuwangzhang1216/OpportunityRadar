"""Notification models for MongoDB."""

from datetime import datetime
from typing import List, Literal, Optional

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


NotificationType = Literal[
    "deadline_reminder",
    "new_match",
    "opportunity_update",
    "system",
    "weekly_digest",
]

NotificationChannel = Literal["in_app", "email", "push"]


class NotificationPreferences(Document):
    """User notification preferences."""

    user_id: Indexed(PydanticObjectId, unique=True)

    # Email notifications
    email_enabled: bool = True
    email_deadline_reminders: bool = True
    email_new_matches: bool = True
    email_weekly_digest: bool = True

    # Deadline reminder timing (days before deadline)
    reminder_days: List[int] = Field(default_factory=lambda: [7, 3, 1])

    # In-app notifications
    in_app_enabled: bool = True
    in_app_deadline_reminders: bool = True
    in_app_new_matches: bool = True

    # Quiet hours (UTC)
    quiet_hours_start: Optional[int] = None  # 0-23 hour
    quiet_hours_end: Optional[int] = None  # 0-23 hour

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "notification_preferences"


class Notification(Document):
    """User notification."""

    user_id: Indexed(PydanticObjectId)
    notification_type: NotificationType
    channel: NotificationChannel = "in_app"

    title: str
    message: str
    action_url: Optional[str] = None

    # Related entities
    opportunity_id: Optional[PydanticObjectId] = None
    match_id: Optional[PydanticObjectId] = None

    # Metadata
    metadata: dict = Field(default_factory=dict)

    # Status
    is_read: bool = False
    is_sent: bool = False  # For email notifications
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None  # Auto-delete after expiration

    class Settings:
        name = "notifications"
        indexes = [
            [("user_id", 1), ("is_read", 1)],
            [("user_id", 1), ("created_at", -1)],
        ]

    def mark_read(self) -> None:
        """Mark notification as read."""
        self.is_read = True
        self.read_at = datetime.utcnow()

    def mark_sent(self) -> None:
        """Mark notification as sent (for email)."""
        self.is_sent = True
        self.sent_at = datetime.utcnow()
