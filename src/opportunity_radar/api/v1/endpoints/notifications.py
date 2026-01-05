"""Notification API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ....models.user import User
from ....core.security import get_current_user
from ....services.notification_service import get_notification_service

router = APIRouter()


class NotificationResponse(BaseModel):
    """Notification response schema."""

    id: str
    notification_type: str
    title: str
    message: str
    action_url: Optional[str] = None
    is_read: bool
    created_at: str
    opportunity_id: Optional[str] = None


class NotificationPreferencesUpdate(BaseModel):
    """Schema for updating notification preferences."""

    email_enabled: Optional[bool] = None
    email_deadline_reminders: Optional[bool] = None
    email_new_matches: Optional[bool] = None
    email_weekly_digest: Optional[bool] = None
    reminder_days: Optional[List[int]] = None
    in_app_enabled: Optional[bool] = None
    in_app_deadline_reminders: Optional[bool] = None
    in_app_new_matches: Optional[bool] = None
    quiet_hours_start: Optional[int] = None
    quiet_hours_end: Optional[int] = None


class NotificationPreferencesResponse(BaseModel):
    """Notification preferences response schema."""

    email_enabled: bool
    email_deadline_reminders: bool
    email_new_matches: bool
    email_weekly_digest: bool
    reminder_days: List[int]
    in_app_enabled: bool
    in_app_deadline_reminders: bool
    in_app_new_matches: bool
    quiet_hours_start: Optional[int]
    quiet_hours_end: Optional[int]


@router.get("", response_model=List[NotificationResponse])
async def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
):
    """Get user notifications."""
    service = get_notification_service()

    notifications = await service.get_user_notifications(
        user_id=str(current_user.id),
        unread_only=unread_only,
        limit=limit,
    )

    return [
        NotificationResponse(
            id=str(n.id),
            notification_type=n.notification_type,
            title=n.title,
            message=n.message,
            action_url=n.action_url,
            is_read=n.is_read,
            created_at=n.created_at.isoformat(),
            opportunity_id=str(n.opportunity_id) if n.opportunity_id else None,
        )
        for n in notifications
    ]


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
):
    """Get count of unread notifications."""
    service = get_notification_service()

    count = await service.get_unread_count(str(current_user.id))

    return {"unread_count": count}


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
):
    """Mark a notification as read."""
    service = get_notification_service()

    success = await service.mark_notification_read(
        notification_id=notification_id,
        user_id=str(current_user.id),
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    return {"success": True}


@router.post("/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
):
    """Mark all notifications as read."""
    service = get_notification_service()

    count = await service.mark_all_read(str(current_user.id))

    return {"marked_read": count}


@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_preferences(
    current_user: User = Depends(get_current_user),
):
    """Get user notification preferences."""
    service = get_notification_service()

    prefs = await service.get_user_preferences(str(current_user.id))

    return NotificationPreferencesResponse(
        email_enabled=prefs.email_enabled,
        email_deadline_reminders=prefs.email_deadline_reminders,
        email_new_matches=prefs.email_new_matches,
        email_weekly_digest=prefs.email_weekly_digest,
        reminder_days=prefs.reminder_days,
        in_app_enabled=prefs.in_app_enabled,
        in_app_deadline_reminders=prefs.in_app_deadline_reminders,
        in_app_new_matches=prefs.in_app_new_matches,
        quiet_hours_start=prefs.quiet_hours_start,
        quiet_hours_end=prefs.quiet_hours_end,
    )


@router.put("/preferences", response_model=NotificationPreferencesResponse)
async def update_preferences(
    updates: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update user notification preferences."""
    service = get_notification_service()

    prefs = await service.update_preferences(
        user_id=str(current_user.id),
        updates=updates.model_dump(exclude_unset=True),
    )

    return NotificationPreferencesResponse(
        email_enabled=prefs.email_enabled,
        email_deadline_reminders=prefs.email_deadline_reminders,
        email_new_matches=prefs.email_new_matches,
        email_weekly_digest=prefs.email_weekly_digest,
        reminder_days=prefs.reminder_days,
        in_app_enabled=prefs.in_app_enabled,
        in_app_deadline_reminders=prefs.in_app_deadline_reminders,
        in_app_new_matches=prefs.in_app_new_matches,
        quiet_hours_start=prefs.quiet_hours_start,
        quiet_hours_end=prefs.quiet_hours_end,
    )
