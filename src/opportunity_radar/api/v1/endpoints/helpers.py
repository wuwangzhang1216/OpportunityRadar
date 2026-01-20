"""Shared helper functions for API endpoints."""

from typing import Any, Optional, Type, TypeVar

from beanie import Document, PydanticObjectId
from beanie.operators import In
from fastapi import HTTPException, status

from ....models.match import Match
from ....models.opportunity import Opportunity
from ....models.user import User

T = TypeVar("T", bound=Document)


async def get_user_document(
    document_class: Type[T],
    document_id: str,
    user: User,
    user_id_field: str = "user_id",
) -> T:
    """
    Get a document by ID and verify it belongs to the current user.

    Raises HTTPException 404 if document not found or doesn't belong to user.
    """
    try:
        document = await document_class.get(PydanticObjectId(document_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{document_class.__name__} not found",
        )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{document_class.__name__} not found",
        )

    # Check ownership
    doc_user_id = getattr(document, user_id_field, None)
    if doc_user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{document_class.__name__} not found",
        )

    return document


async def get_user_match(match_id: str, user: User) -> Match:
    """Get a match by ID that belongs to the current user."""
    return await get_user_document(Match, match_id, user)


def enrich_match_with_opportunity(
    match: Match,
    opportunity: Optional[Opportunity],
    include_description: bool = False,
    include_prize_pool: bool = False,
) -> dict[str, Any]:
    """
    Enrich a match dict with opportunity data.

    Args:
        match: The match document
        opportunity: The related opportunity (can be None)
        include_description: Whether to include opportunity description
        include_prize_pool: Whether to include prize pool

    Returns:
        Enriched match data as dictionary
    """
    match_data = match.model_dump(mode="json")

    # Frontend compatibility aliases
    match_data["score"] = match.overall_score
    match_data["batch_id"] = str(match.opportunity_id) if match.opportunity_id else None

    # Core opportunity data (always included)
    match_data["opportunity_title"] = opportunity.title if opportunity else None
    match_data["opportunity_category"] = opportunity.opportunity_type if opportunity else None
    match_data["deadline"] = (
        opportunity.application_deadline.isoformat()
        if opportunity and opportunity.application_deadline
        else None
    )
    match_data["opportunity_url"] = opportunity.website_url if opportunity else None

    # Optional fields
    if include_description:
        match_data["opportunity_description"] = opportunity.description if opportunity else None

    if include_prize_pool:
        match_data["opportunity_prize_pool"] = opportunity.total_prize_value if opportunity else None

    return match_data


async def fetch_opportunities_by_ids(
    opportunity_ids: list[PydanticObjectId],
) -> dict[PydanticObjectId, Opportunity]:
    """
    Fetch opportunities in bulk and return as a dictionary keyed by ID.

    Args:
        opportunity_ids: List of opportunity IDs to fetch

    Returns:
        Dictionary mapping opportunity ID to Opportunity document
    """
    if not opportunity_ids:
        return {}

    opportunities = await Opportunity.find(In(Opportunity.id, opportunity_ids)).to_list()
    return {opp.id: opp for opp in opportunities}


async def enrich_matches_with_opportunities(
    matches: list[Match],
    include_description: bool = False,
    include_prize_pool: bool = False,
) -> list[dict[str, Any]]:
    """
    Enrich a list of matches with their opportunity data.

    Fetches opportunities in bulk for efficiency.

    Args:
        matches: List of match documents
        include_description: Whether to include opportunity description
        include_prize_pool: Whether to include prize pool

    Returns:
        List of enriched match dictionaries
    """
    if not matches:
        return []

    # Fetch all opportunities in one query
    opp_ids = [m.opportunity_id for m in matches]
    opp_by_id = await fetch_opportunities_by_ids(opp_ids)

    # Enrich each match
    return [
        enrich_match_with_opportunity(
            match=m,
            opportunity=opp_by_id.get(m.opportunity_id),
            include_description=include_description,
            include_prize_pool=include_prize_pool,
        )
        for m in matches
    ]
