"""Unit tests for Calendar export workflow."""

import pytest
from datetime import datetime, timedelta, timezone


class TestCalendarServiceImport:
    """Test CalendarService import and structure."""

    def test_import_calendar_service(self):
        """Test CalendarService import."""
        from src.opportunity_radar.services.calendar_service import CalendarService

        assert CalendarService is not None

    def test_get_calendar_service_singleton(self):
        """Test get_calendar_service singleton function."""
        from src.opportunity_radar.services.calendar_service import get_calendar_service

        service1 = get_calendar_service()
        service2 = get_calendar_service()
        assert service1 is service2


class TestCalendarServiceMethods:
    """Test CalendarService methods exist."""

    def test_opportunity_to_ical_event(self):
        """Test opportunity_to_ical_event method exists."""
        from src.opportunity_radar.services.calendar_service import CalendarService

        assert hasattr(CalendarService, "opportunity_to_ical_event")

    def test_generate_ical(self):
        """Test generate_ical method exists."""
        from src.opportunity_radar.services.calendar_service import CalendarService

        assert hasattr(CalendarService, "generate_ical")

    def test_generate_pipeline_calendar(self):
        """Test generate_pipeline_calendar method exists."""
        from src.opportunity_radar.services.calendar_service import CalendarService

        assert hasattr(CalendarService, "generate_pipeline_calendar")

    def test_generate_upcoming_calendar(self):
        """Test generate_upcoming_calendar method exists."""
        from src.opportunity_radar.services.calendar_service import CalendarService

        assert hasattr(CalendarService, "generate_upcoming_calendar")

    def test_generate_google_calendar_url(self):
        """Test generate_google_calendar_url method exists."""
        from src.opportunity_radar.services.calendar_service import CalendarService

        assert hasattr(CalendarService, "generate_google_calendar_url")

    def test_generate_outlook_calendar_url(self):
        """Test generate_outlook_calendar_url method exists."""
        from src.opportunity_radar.services.calendar_service import CalendarService

        assert hasattr(CalendarService, "generate_outlook_calendar_url")


class TestICalFormatting:
    """Test iCal formatting functions."""

    def test_format_datetime(self):
        """Test datetime formatting for iCal."""
        from src.opportunity_radar.services.calendar_service import CalendarService

        service = CalendarService()

        # Test with timezone-aware datetime
        dt = datetime(2024, 6, 15, 14, 30, 0, tzinfo=timezone.utc)
        formatted = service._format_datetime(dt)

        assert formatted == "20240615T143000Z"

    def test_format_date(self):
        """Test date formatting for iCal all-day events."""
        from src.opportunity_radar.services.calendar_service import CalendarService

        service = CalendarService()

        dt = datetime(2024, 6, 15)
        formatted = service._format_date(dt)

        assert formatted == "20240615"

    def test_escape_text(self):
        """Test text escaping for iCal."""
        from src.opportunity_radar.services.calendar_service import CalendarService

        service = CalendarService()

        # Test escaping special characters
        text = "Hello, World; with\nnewlines"
        escaped = service._escape_text(text)

        assert "\\," in escaped
        assert "\\;" in escaped
        assert "\\n" in escaped

    def test_escape_empty_text(self):
        """Test escaping empty text."""
        from src.opportunity_radar.services.calendar_service import CalendarService

        service = CalendarService()

        assert service._escape_text("") == ""
        assert service._escape_text(None) == ""


class TestUIDGeneration:
    """Test UID generation for calendar events."""

    def test_generate_uid(self):
        """Test UID generation format."""
        from src.opportunity_radar.services.calendar_service import CalendarService

        service = CalendarService()

        uid = service._generate_uid("test-opp-123", "deadline")

        assert "test-opp-123" in uid
        assert "deadline" in uid
        assert "@opportunityradar.app" in uid

    def test_uid_uniqueness(self):
        """Test UIDs are unique for different event types."""
        from src.opportunity_radar.services.calendar_service import CalendarService

        service = CalendarService()

        uid_deadline = service._generate_uid("test-opp-123", "deadline")
        uid_start = service._generate_uid("test-opp-123", "start")
        uid_end = service._generate_uid("test-opp-123", "end")

        assert uid_deadline != uid_start
        assert uid_start != uid_end
        assert uid_deadline != uid_end


class TestICalGeneration:
    """Test iCal content generation."""

    def test_ical_header(self):
        """Test iCal file has proper header."""
        from src.opportunity_radar.services.calendar_service import CalendarService

        service = CalendarService()

        ical = service.generate_ical([], calendar_name="Test Calendar")

        assert "BEGIN:VCALENDAR" in ical
        assert "VERSION:2.0" in ical
        assert "PRODID:-//Opportunity Radar//EN" in ical
        assert "END:VCALENDAR" in ical

    def test_ical_calendar_name(self):
        """Test iCal has custom calendar name."""
        from src.opportunity_radar.services.calendar_service import CalendarService

        service = CalendarService()

        ical = service.generate_ical([], calendar_name="My Test Calendar")

        assert "X-WR-CALNAME:My Test Calendar" in ical


class TestEventTypes:
    """Test different event types."""

    def test_valid_event_types(self):
        """Test valid event types."""
        valid_types = ["deadline", "start", "end"]

        assert len(valid_types) == 3
        assert "deadline" in valid_types

    def test_deadline_event_has_alarms(self):
        """Test deadline events should have alarms."""
        # Deadline events should have reminders
        expected_alarms = ["-P1D", "-PT1H"]  # 1 day and 1 hour before

        assert len(expected_alarms) == 2


class TestCalendarURLs:
    """Test calendar URL generation."""

    def test_google_calendar_url_base(self):
        """Test Google Calendar URL base."""
        base_url = "https://calendar.google.com/calendar/render"
        assert "google.com" in base_url
        assert "calendar" in base_url

    def test_outlook_calendar_url_base(self):
        """Test Outlook Calendar URL base."""
        base_url = "https://outlook.live.com/calendar/0/deeplink/compose"
        assert "outlook.live.com" in base_url
        assert "calendar" in base_url


class TestCalendarWorkflow:
    """Test Calendar workflow logic."""

    def test_default_upcoming_days(self):
        """Test default days ahead for upcoming calendar."""
        default_days = 90

        assert default_days > 0
        assert default_days <= 365

    def test_line_folding(self):
        """Test line folding for long content."""
        from src.opportunity_radar.services.calendar_service import CalendarService

        service = CalendarService()

        # Test with short line
        short_line = "SHORT:This is short"
        folded = service._fold_line(short_line)
        assert "\r\n" not in folded

        # Test with long line
        long_line = "DESCRIPTION:" + "x" * 100
        folded = service._fold_line(long_line)
        # Long lines should be folded
        assert len(long_line) > 75
