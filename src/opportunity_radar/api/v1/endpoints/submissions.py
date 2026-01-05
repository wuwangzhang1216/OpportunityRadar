"""User submissions API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from beanie import PydanticObjectId

from ....models.user import User
from ....models.submission import OpportunitySubmission
from ....schemas.submission import (
    SubmissionCreate,
    SubmissionUpdate,
    SubmissionResponse,
    SubmissionListResponse,
    AdminReviewRequest,
    SubmissionStats,
)
from ....services.submission_service import get_submission_service
from ....core.security import get_current_user, require_admin

router = APIRouter()


def _submission_to_response(submission: OpportunitySubmission) -> SubmissionResponse:
    """Convert submission model to response schema."""
    return SubmissionResponse(
        id=str(submission.id),
        submitted_by=str(submission.submitted_by),
        title=submission.title,
        description=submission.description,
        opportunity_type=submission.opportunity_type,
        format=submission.format,
        website_url=submission.website_url,
        logo_url=submission.logo_url,
        host_name=submission.host_name,
        host_website=submission.host_website,
        location_type=submission.location_type,
        location_city=submission.location_city,
        location_country=submission.location_country,
        application_deadline=submission.application_deadline,
        event_start_date=submission.event_start_date,
        event_end_date=submission.event_end_date,
        themes=submission.themes,
        technologies=submission.technologies,
        total_prize_value=submission.total_prize_value,
        currency=submission.currency,
        team_size_min=submission.team_size_min,
        team_size_max=submission.team_size_max,
        eligibility_notes=submission.eligibility_notes,
        contact_email=submission.contact_email,
        social_links=submission.social_links,
        status=submission.status,
        review_notes=[
            {
                "reviewer_id": str(note.reviewer_id),
                "note": note.note,
                "status_change": note.status_change,
                "created_at": note.created_at,
            }
            for note in submission.review_notes
        ],
        opportunity_id=str(submission.opportunity_id) if submission.opportunity_id else None,
        created_at=submission.created_at,
        updated_at=submission.updated_at,
    )


@router.post("", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def create_submission(
    data: SubmissionCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Submit a new opportunity for review.

    Users can submit opportunities they find that aren't already in the system.
    Submissions go through an admin review process before being added.
    """
    service = get_submission_service()

    submission = await service.create_submission(
        user=current_user,
        data=data.model_dump(exclude_unset=True),
    )

    return _submission_to_response(submission)


@router.get("", response_model=SubmissionListResponse)
async def list_my_submissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """
    List all submissions by the current user.
    """
    service = get_submission_service()

    submissions, total = await service.get_user_submissions(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )

    return SubmissionListResponse(
        items=[_submission_to_response(s) for s in submissions],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{submission_id}", response_model=SubmissionResponse)
async def get_submission(
    submission_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific submission by ID.

    Users can only view their own submissions unless they're an admin.
    """
    service = get_submission_service()

    try:
        submission = await service.get_submission(PydanticObjectId(submission_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    # Check permission
    if submission.submitted_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this submission",
        )

    return _submission_to_response(submission)


@router.patch("/{submission_id}", response_model=SubmissionResponse)
async def update_submission(
    submission_id: str,
    data: SubmissionUpdate,
    current_user: User = Depends(get_current_user),
):
    """
    Update a submission.

    Users can only update their own pending or needs_info submissions.
    """
    service = get_submission_service()

    try:
        submission = await service.get_submission(PydanticObjectId(submission_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    # Check permission
    if submission.submitted_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this submission",
        )

    try:
        submission = await service.update_submission(
            submission=submission,
            data=data.model_dump(exclude_unset=True),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return _submission_to_response(submission)


@router.delete("/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_submission(
    submission_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Delete a submission.

    Users can only delete their own pending submissions.
    """
    service = get_submission_service()

    try:
        submission = await service.get_submission(PydanticObjectId(submission_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    # Check permission
    if submission.submitted_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this submission",
        )

    try:
        await service.delete_submission(submission)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{submission_id}/enhance", response_model=dict)
async def enhance_submission(
    submission_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Use AI to suggest enhancements for a submission.

    Returns suggested themes, technologies, and improvements.
    """
    service = get_submission_service()

    try:
        submission = await service.get_submission(PydanticObjectId(submission_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    # Check permission
    if submission.submitted_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to enhance this submission",
        )

    suggestions = await service.enhance_submission_with_ai(submission)

    return {
        "submission_id": str(submission.id),
        "suggestions": suggestions,
    }


# Admin endpoints

@router.get("/admin/all", response_model=SubmissionListResponse)
async def admin_list_all_submissions(
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_admin),
):
    """
    [Admin] List all submissions with optional status filter.
    """
    service = get_submission_service()

    submissions, total = await service.get_all_submissions(
        status=status,
        skip=skip,
        limit=limit,
    )

    return SubmissionListResponse(
        items=[_submission_to_response(s) for s in submissions],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/admin/pending", response_model=SubmissionListResponse)
async def admin_list_pending_submissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_admin),
):
    """
    [Admin] List all pending submissions awaiting review.
    """
    service = get_submission_service()

    submissions, total = await service.get_pending_submissions(
        skip=skip,
        limit=limit,
    )

    return SubmissionListResponse(
        items=[_submission_to_response(s) for s in submissions],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/admin/stats", response_model=SubmissionStats)
async def admin_submission_stats(
    current_user: User = Depends(require_admin),
):
    """
    [Admin] Get submission statistics.
    """
    service = get_submission_service()
    stats = await service.get_submission_stats()
    return SubmissionStats(**stats)


@router.post("/admin/{submission_id}/review", response_model=SubmissionResponse)
async def admin_review_submission(
    submission_id: str,
    review: AdminReviewRequest,
    current_user: User = Depends(require_admin),
):
    """
    [Admin] Review a submission (approve, reject, or request more info).

    - approved: Creates an opportunity from the submission
    - rejected: Marks submission as rejected with reason
    - needs_info: Requests more information from submitter
    """
    service = get_submission_service()

    # Validate status
    valid_statuses = ["approved", "rejected", "needs_info"]
    if review.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
        )

    try:
        submission = await service.get_submission(PydanticObjectId(submission_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    submission = await service.review_submission(
        submission=submission,
        reviewer=current_user,
        status=review.status,
        note=review.note,
    )

    return _submission_to_response(submission)
