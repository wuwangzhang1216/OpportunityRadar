"""Calendar integration service for exporting opportunities."""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import uuid4

from beanie import PydanticObjectId

from ..models.opportunity import Opportunity
from ..models.pipeline import Pipeline
from ..config import get_settings

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    """Return current UTC time with timezone info."""
    return datetime.now(timezone.utc)


class CalendarService:
    """Service for generating calendar exports."""

    def __init__(self):
        self.settings = get_settings()

    def _format_datetime(self, dt: datetime) -> str:
        """Format datetime for iCal (YYYYMMDDTHHMMSSZ)."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    def _format_date(self, dt: datetime) -> str:
        """Format date for iCal all-day events (YYYYMMDD)."""
        return dt.strftime("%Y%m%d")

    def _escape_text(self, text: str) -> str:
        """Escape text for iCal format."""
        if not text:
            return ""
        # Escape backslashes, newlines, commas, and semicolons
        text = text.replace("\\", "\\\\")
        text = text.replace("\n", "\\n")
        text = text.replace(",", "\\,")
        text = text.replace(";", "\\;")
        return text

    def _fold_line(self, line: str, max_length: int = 75) -> str:
        """Fold long lines according to iCal spec (max 75 octets)."""
        if len(line.encode("utf-8")) <= max_length:
            return line

        result = []
        current_line = ""

        for char in line:
            test_line = current_line + char
            if len(test_line.encode("utf-8")) > max_length:
                result.append(current_line)
                current_line = " " + char  # Continuation line starts with space
            else:
                current_line = test_line

        if current_line:
            result.append(current_line)

        return "\r\n".join(result)

    def _generate_uid(self, opportunity_id: str, event_type: str) -> str:
        """Generate unique identifier for calendar event."""
        return f"{opportunity_id}-{event_type}@opportunityradar.app"

    def opportunity_to_ical_event(
        self,
        opportunity: Opportunity,
        event_type: str = "deadline",
    ) -> str:
        """Convert an opportunity to an iCal VEVENT."""
        lines = []

        # Determine which date to use
        if event_type == "deadline" and opportunity.application_deadline:
            event_date = opportunity.application_deadline
            summary_prefix = "[Deadline] "
        elif event_type == "start" and opportunity.event_start_date:
            event_date = opportunity.event_start_date
            summary_prefix = "[Start] "
        elif event_type == "end" and opportunity.event_end_date:
            event_date = opportunity.event_end_date
            summary_prefix = "[End] "
        else:
            return ""  # No valid date

        uid = self._generate_uid(str(opportunity.id), event_type)
        now = _utc_now()

        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid}")
        lines.append(f"DTSTAMP:{self._format_datetime(now)}")
        lines.append(f"DTSTART:{self._format_datetime(event_date)}")

        # Add end time (1 hour default for deadlines, all day for events)
        if event_type == "deadline":
            end_date = event_date + timedelta(hours=1)
            lines.append(f"DTEND:{self._format_datetime(end_date)}")
        else:
            # All-day event
            end_date = event_date + timedelta(days=1)
            lines.append(f"DTEND;VALUE=DATE:{self._format_date(end_date)}")

        # Summary
        summary = f"{summary_prefix}{self._escape_text(opportunity.title)}"
        lines.append(self._fold_line(f"SUMMARY:{summary}"))

        # Description
        description_parts = []
        if opportunity.description:
            description_parts.append(opportunity.description[:500])
        if opportunity.opportunity_type:
            description_parts.append(f"Type: {opportunity.opportunity_type}")
        if opportunity.total_prize_value:
            description_parts.append(f"Prize: ${opportunity.total_prize_value:,.0f}")
        if opportunity.website_url:
            description_parts.append(f"URL: {opportunity.website_url}")

        if description_parts:
            description = "\\n\\n".join(description_parts)
            lines.append(self._fold_line(f"DESCRIPTION:{self._escape_text(description)}"))

        # URL
        if opportunity.website_url:
            lines.append(f"URL:{opportunity.website_url}")

        # Location
        if opportunity.location_city or opportunity.location_country:
            location_parts = []
            if opportunity.location_city:
                location_parts.append(opportunity.location_city)
            if opportunity.location_country:
                location_parts.append(opportunity.location_country)
            location = ", ".join(location_parts)
            lines.append(f"LOCATION:{self._escape_text(location)}")

        # Categories
        categories = []
        if opportunity.opportunity_type:
            categories.append(opportunity.opportunity_type)
        if opportunity.themes:
            categories.extend(opportunity.themes[:3])
        if categories:
            lines.append(f"CATEGORIES:{','.join(self._escape_text(c) for c in categories)}")

        # Alarm for deadline (1 day before and 1 hour before)
        if event_type == "deadline":
            # 1 day before
            lines.append("BEGIN:VALARM")
            lines.append("TRIGGER:-P1D")
            lines.append("ACTION:DISPLAY")
            lines.append(f"DESCRIPTION:Deadline tomorrow: {self._escape_text(opportunity.title)}")
            lines.append("END:VALARM")

            # 1 hour before
            lines.append("BEGIN:VALARM")
            lines.append("TRIGGER:-PT1H")
            lines.append("ACTION:DISPLAY")
            lines.append(f"DESCRIPTION:Deadline in 1 hour: {self._escape_text(opportunity.title)}")
            lines.append("END:VALARM")

        lines.append("END:VEVENT")

        return "\r\n".join(lines)

    def generate_ical(
        self,
        opportunities: List[Opportunity],
        include_deadlines: bool = True,
        include_events: bool = True,
        calendar_name: str = "Opportunity Radar",
    ) -> str:
        """Generate iCal file content for multiple opportunities."""
        lines = []

        # Calendar header
        lines.append("BEGIN:VCALENDAR")
        lines.append("VERSION:2.0")
        lines.append("PRODID:-//Opportunity Radar//EN")
        lines.append(f"X-WR-CALNAME:{self._escape_text(calendar_name)}")
        lines.append("CALSCALE:GREGORIAN")
        lines.append("METHOD:PUBLISH")

        # Add events
        for opp in opportunities:
            if include_deadlines and opp.application_deadline:
                event = self.opportunity_to_ical_event(opp, "deadline")
                if event:
                    lines.append(event)

            if include_events:
                if opp.event_start_date:
                    event = self.opportunity_to_ical_event(opp, "start")
                    if event:
                        lines.append(event)

                if opp.event_end_date:
                    event = self.opportunity_to_ical_event(opp, "end")
                    if event:
                        lines.append(event)

        lines.append("END:VCALENDAR")

        return "\r\n".join(lines)

    async def generate_pipeline_calendar(
        self,
        pipeline_id: PydanticObjectId,
        include_deadlines: bool = True,
        include_events: bool = True,
    ) -> str:
        """Generate iCal for all opportunities in a pipeline."""
        pipeline = await Pipeline.get(pipeline_id)
        if not pipeline:
            raise ValueError("Pipeline not found")

        # Get all opportunity IDs from pipeline stages
        opportunity_ids = []
        for stage in pipeline.stages:
            opportunity_ids.extend(stage.opportunity_ids)

        # Fetch opportunities
        opportunities = []
        for opp_id in opportunity_ids:
            opp = await Opportunity.get(opp_id)
            if opp:
                opportunities.append(opp)

        return self.generate_ical(
            opportunities,
            include_deadlines=include_deadlines,
            include_events=include_events,
            calendar_name=f"{pipeline.name} - Opportunity Radar",
        )

    async def generate_upcoming_calendar(
        self,
        days_ahead: int = 90,
        opportunity_types: Optional[List[str]] = None,
    ) -> str:
        """Generate iCal for upcoming opportunities."""
        now = _utc_now()
        cutoff = now + timedelta(days=days_ahead)

        query_filter = {
            "is_active": True,
            "$or": [
                {"application_deadline": {"$gte": now, "$lte": cutoff}},
                {"event_start_date": {"$gte": now, "$lte": cutoff}},
            ],
        }

        if opportunity_types:
            query_filter["opportunity_type"] = {"$in": opportunity_types}

        opportunities = await Opportunity.find(query_filter).to_list()

        return self.generate_ical(
            opportunities,
            include_deadlines=True,
            include_events=True,
            calendar_name="Upcoming Opportunities - Opportunity Radar",
        )

    def generate_google_calendar_url(
        self,
        opportunity: Opportunity,
        event_type: str = "deadline",
    ) -> Optional[str]:
        """Generate Google Calendar add event URL."""
        # Determine date
        if event_type == "deadline" and opportunity.application_deadline:
            event_date = opportunity.application_deadline
            title_prefix = "[Deadline] "
        elif event_type == "start" and opportunity.event_start_date:
            event_date = opportunity.event_start_date
            title_prefix = ""
        else:
            return None

        # Format dates for Google Calendar
        start = self._format_datetime(event_date).replace("Z", "")
        end = self._format_datetime(event_date + timedelta(hours=1)).replace("Z", "")

        # Build URL parameters
        import urllib.parse

        title = f"{title_prefix}{opportunity.title}"

        details_parts = []
        if opportunity.description:
            details_parts.append(opportunity.description[:500])
        if opportunity.website_url:
            details_parts.append(f"\n\nMore info: {opportunity.website_url}")
        details = "".join(details_parts)

        location = ""
        if opportunity.location_city or opportunity.location_country:
            location_parts = []
            if opportunity.location_city:
                location_parts.append(opportunity.location_city)
            if opportunity.location_country:
                location_parts.append(opportunity.location_country)
            location = ", ".join(location_parts)

        params = {
            "action": "TEMPLATE",
            "text": title,
            "dates": f"{start}/{end}",
            "details": details,
            "location": location,
        }

        base_url = "https://calendar.google.com/calendar/render"
        query_string = urllib.parse.urlencode(params)

        return f"{base_url}?{query_string}"

    def generate_outlook_calendar_url(
        self,
        opportunity: Opportunity,
        event_type: str = "deadline",
    ) -> Optional[str]:
        """Generate Outlook Calendar add event URL."""
        # Determine date
        if event_type == "deadline" and opportunity.application_deadline:
            event_date = opportunity.application_deadline
            title_prefix = "[Deadline] "
        elif event_type == "start" and opportunity.event_start_date:
            event_date = opportunity.event_start_date
            title_prefix = ""
        else:
            return None

        import urllib.parse

        title = f"{title_prefix}{opportunity.title}"

        # Format for Outlook
        start_iso = event_date.strftime("%Y-%m-%dT%H:%M:%S")
        end_iso = (event_date + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")

        body = ""
        if opportunity.description:
            body = opportunity.description[:500]
        if opportunity.website_url:
            body += f"\n\nMore info: {opportunity.website_url}"

        location = ""
        if opportunity.location_city or opportunity.location_country:
            location_parts = []
            if opportunity.location_city:
                location_parts.append(opportunity.location_city)
            if opportunity.location_country:
                location_parts.append(opportunity.location_country)
            location = ", ".join(location_parts)

        params = {
            "path": "/calendar/action/compose",
            "rru": "addevent",
            "subject": title,
            "startdt": start_iso,
            "enddt": end_iso,
            "body": body,
            "location": location,
        }

        base_url = "https://outlook.live.com/calendar/0/deeplink/compose"
        query_string = urllib.parse.urlencode(params)

        return f"{base_url}?{query_string}"


# Singleton instance
_calendar_service: Optional[CalendarService] = None


def get_calendar_service() -> CalendarService:
    """Get or create the calendar service singleton."""
    global _calendar_service
    if _calendar_service is None:
        _calendar_service = CalendarService()
    return _calendar_service
