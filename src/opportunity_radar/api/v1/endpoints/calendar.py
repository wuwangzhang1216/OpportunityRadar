"""Calendar integration API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from beanie import PydanticObjectId

from ....models.user import User
from ....models.opportunity import Opportunity
from ....models.pipeline import Pipeline
from ....services.calendar_service import get_calendar_service
from ....core.security import get_current_user

router = APIRouter()


@router.get("/opportunity/{opportunity_id}/ical")
async def get_opportunity_ical(
    opportunity_id: str,
    include_deadlines: bool = Query(True, description="Include application deadlines"),
    include_events: bool = Query(True, description="Include event start/end dates"),
):
    """
    Get iCal file for a single opportunity.

    Returns a .ics file that can be imported into any calendar application.
    """
    try:
        opportunity = await Opportunity.get(PydanticObjectId(opportunity_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found",
        )

    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found",
        )

    service = get_calendar_service()
    ical_content = service.generate_ical(
        [opportunity],
        include_deadlines=include_deadlines,
        include_events=include_events,
        calendar_name=opportunity.title,
    )

    return Response(
        content=ical_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f'attachment; filename="{opportunity.slug or opportunity_id}.ics"'
        },
    )


@router.get("/opportunity/{opportunity_id}/google")
async def get_opportunity_google_calendar_url(
    opportunity_id: str,
    event_type: str = Query("deadline", description="Event type: deadline or start"),
):
    """
    Get Google Calendar URL to add an opportunity event.

    Returns a URL that opens Google Calendar with the event pre-filled.
    """
    try:
        opportunity = await Opportunity.get(PydanticObjectId(opportunity_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found",
        )

    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found",
        )

    service = get_calendar_service()
    url = service.generate_google_calendar_url(opportunity, event_type)

    if not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No {event_type} date available for this opportunity",
        )

    return {"url": url}


@router.get("/opportunity/{opportunity_id}/outlook")
async def get_opportunity_outlook_calendar_url(
    opportunity_id: str,
    event_type: str = Query("deadline", description="Event type: deadline or start"),
):
    """
    Get Outlook Calendar URL to add an opportunity event.

    Returns a URL that opens Outlook Calendar with the event pre-filled.
    """
    try:
        opportunity = await Opportunity.get(PydanticObjectId(opportunity_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found",
        )

    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found",
        )

    service = get_calendar_service()
    url = service.generate_outlook_calendar_url(opportunity, event_type)

    if not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No {event_type} date available for this opportunity",
        )

    return {"url": url}


@router.get("/pipeline/{pipeline_id}/ical")
async def get_pipeline_ical(
    pipeline_id: str,
    include_deadlines: bool = Query(True, description="Include application deadlines"),
    include_events: bool = Query(True, description="Include event start/end dates"),
    current_user: User = Depends(get_current_user),
):
    """
    Get iCal file for all opportunities in a pipeline.

    Requires authentication. Users can only export their own pipelines.
    """
    try:
        pipeline = await Pipeline.get(PydanticObjectId(pipeline_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found",
        )

    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found",
        )

    # Check ownership
    if pipeline.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this pipeline",
        )

    service = get_calendar_service()

    try:
        ical_content = await service.generate_pipeline_calendar(
            pipeline_id=pipeline.id,
            include_deadlines=include_deadlines,
            include_events=include_events,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return Response(
        content=ical_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f'attachment; filename="{pipeline.slug or pipeline_id}-calendar.ics"'
        },
    )


@router.get("/upcoming/ical")
async def get_upcoming_ical(
    days_ahead: int = Query(90, ge=1, le=365, description="Number of days to look ahead"),
    opportunity_types: Optional[List[str]] = Query(None, description="Filter by opportunity types"),
    include_deadlines: bool = Query(True, description="Include application deadlines"),
    include_events: bool = Query(True, description="Include event start/end dates"),
):
    """
    Get iCal file for all upcoming opportunities.

    Returns events for the next N days (default 90).
    """
    service = get_calendar_service()

    ical_content = await service.generate_upcoming_calendar(
        days_ahead=days_ahead,
        opportunity_types=opportunity_types,
    )

    return Response(
        content=ical_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": 'attachment; filename="upcoming-opportunities.ics"'
        },
    )


@router.get("/subscribe-url")
async def get_subscription_url(
    current_user: User = Depends(get_current_user),
):
    """
    Get calendar subscription URLs for the current user.

    Returns URLs that can be used to subscribe to calendars in external apps.
    """
    from ....config import get_settings

    settings = get_settings()
    base_url = settings.api_base_url or "https://api.opportunityradar.app"

    # Generate URLs (in a real app, these would include auth tokens)
    return {
        "upcoming_ical": f"{base_url}/api/v1/calendar/upcoming/ical",
        "info": "Add these URLs to your calendar app to stay updated with opportunities.",
        "instructions": {
            "google": "In Google Calendar, go to Settings > Add calendar > From URL",
            "outlook": "In Outlook, go to Add calendar > Subscribe from web",
            "apple": "In Calendar app, go to File > New Calendar Subscription",
        },
    }
