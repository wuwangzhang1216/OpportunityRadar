"""Notification service for deadline reminders and alerts."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from openai import OpenAI

from ..config import get_settings
from ..models.notification import Notification, NotificationPreferences
from ..models.match import Match
from ..models.opportunity import Opportunity
from ..models.user import User

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications and deadline reminders."""

    def __init__(self):
        settings = get_settings()
        self.openai_client = OpenAI(api_key=settings.openai_api_key)

    async def get_user_preferences(
        self,
        user_id: str,
    ) -> NotificationPreferences:
        """Get or create user notification preferences."""
        from beanie import PydanticObjectId

        user_oid = PydanticObjectId(user_id)

        prefs = await NotificationPreferences.find_one(
            NotificationPreferences.user_id == user_oid
        )

        if not prefs:
            prefs = NotificationPreferences(user_id=user_oid)
            await prefs.insert()

        return prefs

    async def update_preferences(
        self,
        user_id: str,
        updates: Dict,
    ) -> NotificationPreferences:
        """Update user notification preferences."""
        from beanie import PydanticObjectId

        prefs = await self.get_user_preferences(user_id)

        for key, value in updates.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)

        prefs.updated_at = datetime.utcnow()
        await prefs.save()

        return prefs

    async def create_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        channel: str = "in_app",
        opportunity_id: Optional[str] = None,
        match_id: Optional[str] = None,
        action_url: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Notification:
        """Create a new notification."""
        from beanie import PydanticObjectId

        notification = Notification(
            user_id=PydanticObjectId(user_id),
            notification_type=notification_type,
            channel=channel,
            title=title,
            message=message,
            action_url=action_url,
            opportunity_id=PydanticObjectId(opportunity_id) if opportunity_id else None,
            match_id=PydanticObjectId(match_id) if match_id else None,
            metadata=metadata or {},
        )

        await notification.insert()
        logger.info(f"Created notification for user {user_id}: {title}")

        return notification

    async def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[Notification]:
        """Get notifications for a user."""
        from beanie import PydanticObjectId

        user_oid = PydanticObjectId(user_id)

        query = Notification.find(Notification.user_id == user_oid)

        if unread_only:
            query = query.find(Notification.is_read == False)  # noqa: E712

        notifications = await query.sort("-created_at").limit(limit).to_list()

        return notifications

    async def mark_notification_read(
        self,
        notification_id: str,
        user_id: str,
    ) -> bool:
        """Mark a notification as read."""
        from beanie import PydanticObjectId

        notification = await Notification.find_one(
            Notification.id == PydanticObjectId(notification_id),
            Notification.user_id == PydanticObjectId(user_id),
        )

        if notification:
            notification.mark_read()
            await notification.save()
            return True

        return False

    async def mark_all_read(self, user_id: str) -> int:
        """Mark all notifications as read for a user."""
        from beanie import PydanticObjectId

        result = await Notification.find(
            Notification.user_id == PydanticObjectId(user_id),
            Notification.is_read == False,  # noqa: E712
        ).update_many(
            {"$set": {"is_read": True, "read_at": datetime.utcnow()}}
        )

        return result.modified_count

    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications."""
        from beanie import PydanticObjectId

        return await Notification.find(
            Notification.user_id == PydanticObjectId(user_id),
            Notification.is_read == False,  # noqa: E712
        ).count()

    async def check_deadline_reminders(self) -> Dict:
        """
        Check all bookmarked matches for upcoming deadlines and send reminders.

        Returns:
            Statistics about reminders sent
        """
        stats = {
            "users_checked": 0,
            "reminders_sent": 0,
            "errors": 0,
        }

        # Get all users with bookmarked matches
        bookmarked_matches = await Match.find(
            Match.is_bookmarked == True  # noqa: E712
        ).to_list()

        # Group by user
        user_matches: Dict[str, List[Match]] = {}
        for match in bookmarked_matches:
            user_id = str(match.user_id)
            if user_id not in user_matches:
                user_matches[user_id] = []
            user_matches[user_id].append(match)

        now = datetime.utcnow()

        for user_id, matches in user_matches.items():
            stats["users_checked"] += 1

            try:
                # Get user preferences
                prefs = await self.get_user_preferences(user_id)

                if not prefs.in_app_deadline_reminders:
                    continue

                reminder_days = prefs.reminder_days or [7, 3, 1]

                for match in matches:
                    opportunity = await Opportunity.get(match.opportunity_id)
                    if not opportunity:
                        continue

                    # Get deadline from opportunity timelines
                    deadline = self._extract_deadline(opportunity)
                    if not deadline:
                        continue

                    days_until = (deadline - now).days

                    # Check if we should send a reminder
                    if days_until in reminder_days:
                        # Check if reminder already sent today
                        existing = await Notification.find_one(
                            Notification.user_id == match.user_id,
                            Notification.opportunity_id == opportunity.id,
                            Notification.notification_type == "deadline_reminder",
                            Notification.created_at >= now.replace(hour=0, minute=0, second=0),
                        )

                        if existing:
                            continue  # Already sent today

                        # Generate personalized reminder message
                        message = await self._generate_reminder_message(
                            opportunity,
                            days_until,
                        )

                        await self.create_notification(
                            user_id=user_id,
                            notification_type="deadline_reminder",
                            title=f"Deadline in {days_until} day{'s' if days_until != 1 else ''}: {opportunity.title}",
                            message=message,
                            opportunity_id=str(opportunity.id),
                            match_id=str(match.id),
                            action_url=f"/opportunities/{opportunity.id}",
                            metadata={
                                "days_until_deadline": days_until,
                                "deadline": deadline.isoformat(),
                            },
                        )

                        stats["reminders_sent"] += 1

            except Exception as e:
                logger.error(f"Error checking deadlines for user {user_id}: {e}")
                stats["errors"] += 1

        logger.info(
            f"Deadline check complete: {stats['reminders_sent']} reminders sent, "
            f"{stats['users_checked']} users checked"
        )

        return stats

    def _extract_deadline(self, opportunity: Opportunity) -> Optional[datetime]:
        """Extract submission deadline from opportunity."""
        if not opportunity.timelines:
            return None

        for timeline in opportunity.timelines:
            if isinstance(timeline, dict):
                deadline_str = (
                    timeline.get("submission_deadline") or
                    timeline.get("registration_closes_at") or
                    timeline.get("deadline")
                )
                if deadline_str:
                    try:
                        return datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        pass

        return None

    async def _generate_reminder_message(
        self,
        opportunity: Opportunity,
        days_until: int,
    ) -> str:
        """Generate a personalized reminder message using AI."""
        try:
            urgency = "urgent" if days_until <= 1 else "important" if days_until <= 3 else "upcoming"

            prompt = f"""Generate a brief, encouraging reminder message (max 2 sentences) for a deadline notification.

Opportunity: {opportunity.title}
Type: {opportunity.opportunity_type}
Days until deadline: {days_until}
Urgency: {urgency}

The message should be motivating and actionable. Don't mention the exact number of days (that's in the title)."""

            response = self.openai_client.responses.create(
                model="gpt-5.2",
                input=prompt,
            )

            return response.output_text.strip()

        except Exception as e:
            logger.warning(f"Failed to generate AI message: {e}")
            # Fallback message
            if days_until <= 1:
                return "Don't miss out! Make sure to submit your application today."
            elif days_until <= 3:
                return "Time is running short. Consider finalizing your application soon."
            else:
                return "Mark your calendar and start preparing your application."

    async def send_new_match_notification(
        self,
        user_id: str,
        opportunity: Opportunity,
        match_score: float,
    ) -> Optional[Notification]:
        """Send notification for a new high-quality match."""
        prefs = await self.get_user_preferences(user_id)

        if not prefs.in_app_new_matches:
            return None

        # Only notify for high-quality matches
        if match_score < 0.7:
            return None

        message = f"Score: {int(match_score * 100)}% - This opportunity aligns well with your profile!"

        return await self.create_notification(
            user_id=user_id,
            notification_type="new_match",
            title=f"New match: {opportunity.title}",
            message=message,
            opportunity_id=str(opportunity.id),
            action_url=f"/matches",
        )

    async def cleanup_old_notifications(
        self,
        days_to_keep: int = 30,
    ) -> int:
        """Delete old read notifications."""
        cutoff = datetime.utcnow() - timedelta(days=days_to_keep)

        result = await Notification.find(
            Notification.is_read == True,  # noqa: E712
            Notification.created_at < cutoff,
        ).delete()

        logger.info(f"Cleaned up {result.deleted_count} old notifications")
        return result.deleted_count


# Singleton instance
_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get or create the notification service singleton."""
    global _service
    if _service is None:
        _service = NotificationService()
    return _service
