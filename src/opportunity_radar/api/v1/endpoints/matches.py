"""Match endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from beanie import PydanticObjectId

from ....core.security import get_current_user
from ....models.user import User
from ....models.match import Match

router = APIRouter()


@router.get("")
async def list_matches(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    dismissed: Optional[bool] = Query(None),
    bookmarked: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
):
    """
    Get matches for current user.

    - **dismissed**: Filter by dismissed status
    - **bookmarked**: Filter by bookmarked status
    """
    query = {"user_id": current_user.id}
    if dismissed is not None:
        query["is_dismissed"] = dismissed
    if bookmarked is not None:
        query["is_bookmarked"] = bookmarked

    matches = await Match.find(query).sort(-Match.overall_score).skip(offset).limit(limit).to_list()
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

    Returns the highest scoring matches that are not dismissed.
    """
    matches = await Match.find(
        Match.user_id == current_user.id,
        Match.is_dismissed == False
    ).sort(-Match.overall_score).limit(limit).to_list()

    return {"items": matches, "count": len(matches)}


@router.get("/by-batch/{batch_id}")
async def get_match_by_batch(
    batch_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get match for a specific opportunity/batch by batch_id.

    Returns the match record including score breakdown and eligibility info.
    """
    try:
        match = await Match.find_one(
            Match.user_id == current_user.id,
            Match.batch_id == PydanticObjectId(batch_id),
        )
    except Exception:
        match = None

    if not match:
        return None

    return match


@router.get("/stats")
async def get_match_stats(
    current_user: User = Depends(get_current_user),
):
    """Get match statistics for current user."""
    # Get counts
    total_count = await Match.find(Match.user_id == current_user.id).count()
    bookmarked_count = await Match.find(
        Match.user_id == current_user.id, Match.is_bookmarked == True
    ).count()
    dismissed_count = await Match.find(
        Match.user_id == current_user.id, Match.is_dismissed == True
    ).count()

    # Calculate average score
    all_matches = await Match.find(Match.user_id == current_user.id).to_list()
    avg_score = (
        sum(m.overall_score for m in all_matches) / len(all_matches)
        if all_matches
        else 0
    )

    return {
        "total_matches": total_count,
        "bookmarked": bookmarked_count,
        "dismissed": dismissed_count,
        "active": total_count - dismissed_count,
        "average_score": round(avg_score, 3),
    }


@router.post("/{match_id}/dismiss")
async def dismiss_match(
    match_id: str,
    current_user: User = Depends(get_current_user),
):
    """Dismiss a match (hide from recommendations)."""
    try:
        match = await Match.get(PydanticObjectId(match_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    if not match or match.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    match.is_dismissed = True
    await match.save()

    return {"message": "Match dismissed", "match_id": match_id}


@router.post("/{match_id}/bookmark")
async def bookmark_match(
    match_id: str,
    current_user: User = Depends(get_current_user),
):
    """Bookmark a match (save for later)."""
    try:
        match = await Match.get(PydanticObjectId(match_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    if not match or match.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    match.is_bookmarked = True
    await match.save()

    return {"message": "Match bookmarked", "match_id": match_id}


@router.post("/{match_id}/unbookmark")
async def unbookmark_match(
    match_id: str,
    current_user: User = Depends(get_current_user),
):
    """Remove bookmark from a match."""
    try:
        match = await Match.get(PydanticObjectId(match_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    if not match or match.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    match.is_bookmarked = False
    await match.save()

    return {"message": "Bookmark removed", "match_id": match_id}


@router.post("/{match_id}/restore")
async def restore_match(
    match_id: str,
    current_user: User = Depends(get_current_user),
):
    """Restore a dismissed match."""
    try:
        match = await Match.get(PydanticObjectId(match_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    if not match or match.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    match.is_dismissed = False
    await match.save()

    return {"message": "Match restored", "match_id": match_id}
