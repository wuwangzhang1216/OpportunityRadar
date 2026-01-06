"""Match endpoints."""

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from beanie import PydanticObjectId
from beanie.operators import In

from ....core.security import get_current_user
from ....models.user import User
from ....models.match import Match
from ....models.opportunity import Opportunity
from ....models.profile import Profile

router = APIRouter()


@router.get("")
async def list_matches(
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    offset: Optional[int] = Query(None, ge=0, description="Deprecated: use skip instead"),
    dismissed: Optional[bool] = Query(None),
    bookmarked: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
):
    """
    Get matches for current user with enriched opportunity data.

    - **skip**: Number of records to skip (pagination)
    - **dismissed**: Filter by dismissed status
    - **bookmarked**: Filter by bookmarked status
    """
    # Support both skip and offset for backwards compatibility
    actual_offset = offset if offset is not None else skip

    query = {"user_id": current_user.id}
    if dismissed is not None:
        query["is_dismissed"] = dismissed
    if bookmarked is not None:
        query["is_bookmarked"] = bookmarked

    matches = await Match.find(query).sort(-Match.overall_score).skip(actual_offset).limit(limit).to_list()
    total = await Match.find(query).count()

    if not matches:
        return {
            "items": [],
            "total": total,
            "limit": limit,
            "offset": actual_offset,
        }

    # Fetch related opportunities in bulk for enrichment
    opp_ids = [m.opportunity_id for m in matches]
    opps = await Opportunity.find(In(Opportunity.id, opp_ids)).to_list()
    opp_by_id = {o.id: o for o in opps}

    # Enrich matches with opportunity data (same as /top endpoint)
    items = []
    for m in matches:
        opp = opp_by_id.get(m.opportunity_id)
        match_data = m.model_dump(mode="json")
        # Frontend compatibility aliases
        match_data["score"] = m.overall_score
        match_data["batch_id"] = str(m.opportunity_id) if m.opportunity_id else None
        # Enriched opportunity data
        match_data["opportunity_title"] = opp.title if opp else None
        match_data["opportunity_category"] = opp.opportunity_type if opp else None
        match_data["opportunity_description"] = opp.description if opp else None
        match_data["deadline"] = opp.application_deadline.isoformat() if opp and opp.application_deadline else None
        match_data["opportunity_url"] = opp.website_url if opp else None
        match_data["opportunity_prize_pool"] = opp.total_prize_value if opp else None
        items.append(match_data)

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": actual_offset,
    }


@router.get("/top")
async def get_top_matches(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
):
    """
    Get top N matches with enriched opportunity data.

    Returns the highest scoring matches that are not dismissed,
    including opportunity details (title, category, deadline, url).
    """
    matches = await Match.find(
        Match.user_id == current_user.id,
        Match.is_dismissed == False
    ).sort(-Match.overall_score).limit(limit).to_list()

    if not matches:
        return {"items": [], "count": 0}

    # Fetch related opportunities in bulk
    opp_ids = [m.opportunity_id for m in matches]
    opps = await Opportunity.find(In(Opportunity.id, opp_ids)).to_list()
    opp_by_id = {o.id: o for o in opps}

    # Enrich matches with opportunity data
    items = []
    for m in matches:
        opp = opp_by_id.get(m.opportunity_id)
        match_data = m.model_dump(mode="json")
        # Frontend compatibility aliases
        match_data["score"] = m.overall_score
        match_data["batch_id"] = str(m.opportunity_id) if m.opportunity_id else None
        # Enriched opportunity data
        match_data["opportunity_title"] = opp.title if opp else None
        match_data["opportunity_category"] = opp.opportunity_type if opp else None
        match_data["deadline"] = opp.application_deadline.isoformat() if opp and opp.application_deadline else None
        match_data["opportunity_url"] = opp.website_url if opp else None
        items.append(match_data)

    return {"items": items, "count": len(items)}


@router.get("/by-batch/{batch_id}")
async def get_match_by_batch(
    batch_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get match for a specific opportunity by batch_id (which maps to opportunity_id).

    Returns the match record including score breakdown and eligibility info.
    The batch_id parameter is kept for frontend compatibility but maps to opportunity_id.
    """
    try:
        match = await Match.find_one(
            Match.user_id == current_user.id,
            Match.opportunity_id == PydanticObjectId(batch_id),
        )
    except Exception:
        match = None

    if not match:
        return None

    # Convert to dict and add computed scores from breakdown if not present
    result = match.model_dump(mode="json")

    # Extract scores from score_breakdown if individual scores are None
    breakdown = match.score_breakdown or {}
    factors = breakdown.get("factors", {})
    eligibility = breakdown.get("eligibility", {})

    # Map factor names to frontend field names
    # rule_score = compute from eligibility checks (all True = 1.0)
    if result.get("rule_score") is None:
        if eligibility:
            # Count how many eligibility checks pass
            checks = [eligibility.get("team_size", True), eligibility.get("funding_stage", True), eligibility.get("location", True)]
            result["rule_score"] = sum(1 for c in checks if c) / len(checks) if checks else 1.0
        else:
            result["rule_score"] = 1.0 if breakdown.get("is_eligible", True) else 0.0

    # time_score = deadline factor or use recency_boost as proxy
    if result.get("time_score") is None:
        if "deadline" in factors:
            result["time_score"] = factors["deadline"].get("score", 0)
        elif "time" in factors:
            result["time_score"] = factors["time"].get("score", 0)
        elif "recency_boost" in breakdown:
            # New format: recency_boost indicates how recent/timely the opportunity is
            # Scale it up since recency_boost is typically small (0-0.05)
            # If recency > 0, the opportunity is recent and timely
            recency = breakdown.get("recency_boost", 0)
            # Map recency_boost to a reasonable time_score
            # 0.02+ is recent, give high score; 0 means older
            result["time_score"] = min(1.0, 0.7 + recency * 10) if recency > 0 else 0.5

    # team_score = goals_alignment, track_record, or derive from semantic similarity
    if result.get("team_score") is None:
        if "goals_alignment" in factors:
            result["team_score"] = factors["goals_alignment"].get("score", 0)
        elif "track_record" in factors:
            result["team_score"] = factors["track_record"].get("score", 0)
        elif "team" in factors:
            result["team_score"] = factors["team"].get("score", 0)
        else:
            # New format doesn't have team_score - derive from semantic score
            # If semantic match is high, team fit is likely good too
            semantic = breakdown.get("semantic_score") or match.semantic_score or 0
            # Use semantic as a proxy for overall fit including team
            result["team_score"] = semantic * 0.9  # Slightly lower than semantic

    return result


@router.post("/calculate")
async def calculate_matches(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Trigger match calculation for current user.

    Matches are computed asynchronously in the background.
    Use GET /matches/status to poll for completion.
    """
    profile = await Profile.find_one(Profile.user_id == current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile not found. Please complete onboarding first.",
        )

    async def compute_matches_task():
        from ....services.mongo_matching_service import MongoMatchingService
        service = MongoMatchingService()
        matches = await service.compute_matches_for_profile(
            str(profile.id), limit=100, min_score=0.0
        )
        await service.save_matches(str(current_user.id), matches)

    background_tasks.add_task(compute_matches_task)

    return {"message": "Match calculation started", "status": "processing"}


@router.get("/status")
async def get_match_status(
    current_user: User = Depends(get_current_user),
):
    """
    Get match calculation status for current user.

    Used by frontend polling to know when matches are ready.
    Returns:
    - has_profile: Whether user has a profile
    - has_embedding: Whether profile has an embedding computed
    - match_count: Number of matches found
    - status: "ready" | "calculating" | "no_profile"
    """
    total_count = await Match.find(Match.user_id == current_user.id).count()
    profile = await Profile.find_one(Profile.user_id == current_user.id)

    has_profile = profile is not None
    has_embedding = profile and profile.embedding is not None

    # Determine status - detect in-progress recalculation
    if not has_profile:
        status_value = "no_profile"
    elif not has_embedding:
        status_value = "no_profile"
    elif profile.last_match_computation is None:
        # Never computed yet
        status_value = "calculating"
    elif profile.updated_at > profile.last_match_computation:
        # Profile updated since last computation - recalculating
        status_value = "calculating"
    elif total_count > 0:
        status_value = "ready"
    else:
        status_value = "calculating"

    return {
        "has_profile": has_profile,
        "has_embedding": has_embedding,
        "match_count": total_count,
        "status": status_value,
    }


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
