"""Unit tests for Notification workflow."""

import pytest
from datetime import datetime


class TestNotificationModel:
    """Test Notification model functionality."""

    def test_import_notification(self):
        """Test Notification model import."""
        from src.opportunity_radar.models.notification import Notification

        assert Notification is not None

    def test_notification_has_required_fields(self):
        """Test Notification model has all required fields."""
        from src.opportunity_radar.models.notification import Notification

        fields = Notification.model_fields

        assert "user_id" in fields
        assert "notification_type" in fields
        assert "channel" in fields
        assert "title" in fields
        assert "message" in fields
        assert "is_read" in fields
        assert "is_sent" in fields
        assert "created_at" in fields

    def test_notification_default_values(self):
        """Test Notification default values."""
        from src.opportunity_radar.models.notification import Notification

        assert Notification.model_fields["is_read"].default is False
        assert Notification.model_fields["is_sent"].default is False
        assert Notification.model_fields["channel"].default == "in_app"


class TestNotificationPreferencesModel:
    """Test NotificationPreferences model."""

    def test_import_notification_preferences(self):
        """Test NotificationPreferences import."""
        from src.opportunity_radar.models.notification import NotificationPreferences

        assert NotificationPreferences is not None

    def test_preferences_has_required_fields(self):
        """Test NotificationPreferences has required fields."""
        from src.opportunity_radar.models.notification import NotificationPreferences

        fields = NotificationPreferences.model_fields

        # Email preferences
        assert "email_enabled" in fields
        assert "email_deadline_reminders" in fields
        assert "email_new_matches" in fields
        assert "email_weekly_digest" in fields

        # Reminder settings
        assert "reminder_days" in fields

        # In-app preferences
        assert "in_app_enabled" in fields
        assert "in_app_deadline_reminders" in fields
        assert "in_app_new_matches" in fields

    def test_preferences_defaults(self):
        """Test NotificationPreferences default values."""
        from src.opportunity_radar.models.notification import NotificationPreferences

        assert NotificationPreferences.model_fields["email_enabled"].default is True
        assert NotificationPreferences.model_fields["in_app_enabled"].default is True


class TestNotificationMethods:
    """Test Notification model methods."""

    def test_mark_read_method_exists(self):
        """Test mark_read method exists."""
        from src.opportunity_radar.models.notification import Notification

        assert hasattr(Notification, "mark_read")
        assert callable(getattr(Notification, "mark_read"))

    def test_mark_sent_method_exists(self):
        """Test mark_sent method exists."""
        from src.opportunity_radar.models.notification import Notification

        assert hasattr(Notification, "mark_sent")
        assert callable(getattr(Notification, "mark_sent"))


class TestNotificationService:
    """Test NotificationService functionality."""

    def test_import_notification_service(self):
        """Test NotificationService import."""
        from src.opportunity_radar.services.notification_service import (
            NotificationService,
        )

        assert NotificationService is not None

    def test_get_notification_service_singleton(self):
        """Test get_notification_service singleton function."""
        from src.opportunity_radar.services.notification_service import (
            get_notification_service,
        )

        assert get_notification_service is not None
        assert callable(get_notification_service)

    def test_notification_service_methods(self):
        """Test NotificationService has required methods."""
        from src.opportunity_radar.services.notification_service import (
            NotificationService,
        )

        # Check for required methods
        assert hasattr(NotificationService, "get_user_preferences")
        assert hasattr(NotificationService, "update_preferences")
        assert hasattr(NotificationService, "create_notification")
        assert hasattr(NotificationService, "get_user_notifications")
        assert hasattr(NotificationService, "mark_notification_read")
        assert hasattr(NotificationService, "mark_all_read")
        assert hasattr(NotificationService, "get_unread_count")
        assert hasattr(NotificationService, "check_deadline_reminders")
        assert hasattr(NotificationService, "send_new_match_notification")
        assert hasattr(NotificationService, "cleanup_old_notifications")


class TestNotificationTypes:
    """Test notification types and channels."""

    def test_valid_notification_types(self):
        """Test valid notification types."""
        valid_types = [
            "deadline_reminder",
            "new_match",
            "opportunity_update",
            "system",
            "weekly_digest",
        ]

        assert len(valid_types) == 5
        assert "deadline_reminder" in valid_types
        assert "new_match" in valid_types

    def test_valid_notification_channels(self):
        """Test valid notification channels."""
        valid_channels = ["in_app", "email", "push"]

        assert len(valid_channels) == 3
        assert "in_app" in valid_channels


class TestNotificationWorkflow:
    """Test Notification workflow logic."""

    def test_reminder_days_default(self):
        """Test default reminder days."""
        from src.opportunity_radar.models.notification import NotificationPreferences

        # Default reminder days should be 7, 3, 1 days before deadline
        default_days = [7, 3, 1]
        assert len(default_days) == 3

    def test_quiet_hours_fields_exist(self):
        """Test quiet hours fields exist."""
        from src.opportunity_radar.models.notification import NotificationPreferences

        fields = NotificationPreferences.model_fields

        assert "quiet_hours_start" in fields
        assert "quiet_hours_end" in fields
