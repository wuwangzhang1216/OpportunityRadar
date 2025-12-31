"""Match endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from beanie import PydanticObjectId

from ....core.security import get_current_user
from ....models.user import User
from ....models.profile import Profile
from ....models.match import Match

router = APIRouter()


async def _get_user_profile(user: User):
    """Helper to get user's profile or raise 404."""
    profile = await Profile.find_one(Profile.user_id == user.id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Please create a profile first.",
        )

    return profile


@router.get("")
async def list_matches(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
):
    """
    Get matches for current user.

    - **status**: Filter by status (pending, interested, applied, dismissed)
    """
    profile = await _get_user_profile(current_user)

    query = {"profile_id": profile.id}
    if status_filter:
        query["status"] = status_filter

    matches = await Match.find(query).skip(offset).limit(limit).to_list()
    total = await Match.find(query).count()

    return {
        "items": matches,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/top")
async def get_top_matches(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
):
    """
    Get top N matches with detailed reasons and score breakdown.

    Returns the highest scoring matches that are still pending (not dismissed).
    """
    profile = await _get_user_profile(current_user)

    matches = await Match.find(
        Match.profile_id == profile.id,
        Match.status == "pending"
    ).sort(-Match.score).limit(limit).to_list()

    return {"items": matches, "count": len(matches)}


@router.get("/stats")
async def get_match_stats(
    current_user: User = Depends(get_current_user),
):
    """Get match statistics for current user."""
    profile = await _get_user_profile(current_user)

    # Get counts by status
    pending_count = await Match.find(
        Match.profile_id == profile.id, Match.status == "pending"
    ).count()
    interested_count = await Match.find(
        Match.profile_id == profile.id, Match.status == "interested"
    ).count()
    applied_count = await Match.find(
        Match.profile_id == profile.id, Match.status == "applied"
    ).count()
    dismissed_count = await Match.find(
        Match.profile_id == profile.id, Match.status == "dismissed"
    ).count()

    total = pending_count + interested_count + applied_count + dismissed_count

    # Calculate average score
    all_matches = await Match.find(Match.profile_id == profile.id).to_list()
    avg_score = (
        sum(m.score for m in all_matches) / len(all_matches)
        if all_matches
        else 0
    )

    return {
        "total_matches": total,
        "by_status": {
            "pending": pending_count,
            "interested": interested_count,
            "applied": applied_count,
            "dismissed": dismissed_count,
        },
        "average_score": round(avg_score, 3),
    }


@router.post("/{match_id}/dismiss")
async def dismiss_match(
    match_id: str,
    current_user: User = Depends(get_current_user),
):
    """Dismiss a match (hide from recommendations)."""
    profile = await _get_user_profile(current_user)

    try:
        match = await Match.get(PydanticObjectId(match_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    if not match or match.profile_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    match.status = "dismissed"
    await match.save()

    return {"message": "Match dismissed", "match_id": match_id}


@router.post("/{match_id}/interested")
async def mark_interested(
    match_id: str,
    current_user: User = Depends(get_current_user),
):
    """Mark a match as interested (save for later)."""
    profile = await _get_user_profile(current_user)

    try:
        match = await Match.get(PydanticObjectId(match_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    if not match or match.profile_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    match.status = "interested"
    await match.save()

    return {"message": "Marked as interested", "match_id": match_id}


@router.post("/{match_id}/apply")
async def mark_applied(
    match_id: str,
    current_user: User = Depends(get_current_user),
):
    """Mark a match as applied."""
    profile = await _get_user_profile(current_user)

    try:
        match = await Match.get(PydanticObjectId(match_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    if not match or match.profile_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    match.status = "applied"
    await match.save()

    return {"message": "Marked as applied", "match_id": match_id}


@router.post("/{match_id}/restore")
async def restore_match(
    match_id: str,
    current_user: User = Depends(get_current_user),
):
    """Restore a dismissed match back to pending."""
    profile = await _get_user_profile(current_user)

    try:
        match = await Match.get(PydanticObjectId(match_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    if not match or match.profile_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    match.status = "pending"
    await match.save()

    return {"message": "Match restored", "match_id": match_id}
