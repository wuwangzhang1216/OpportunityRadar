"""Opportunities API endpoints."""

from typing import List, Optional, Any, Dict

from fastapi import APIRouter, Query, HTTPException, status
from beanie import PydanticObjectId

from ....models.opportunity import Opportunity, Host

router = APIRouter()


def transform_opportunity_for_frontend(opp: Opportunity) -> Dict[str, Any]:
    """Transform opportunity data to match frontend field expectations."""
    data = opp.model_dump()

    # Add frontend-expected field mappings
    data["category"] = opp.opportunity_type
    data["deadline"] = opp.application_deadline
    data["prize_pool"] = opp.total_prize_value
    data["team_min"] = opp.team_size_min
    data["team_max"] = opp.team_size_max
    data["url"] = opp.website_url or opp.source_url

    # Combine themes and technologies into tags
    tags = list(opp.themes or [])
    if opp.technologies:
        tags.extend(opp.technologies)
    data["tags"] = tags

    # Build regions array from location fields
    regions = []
    if opp.location_region:
        regions.append(opp.location_region)
    if opp.location_country:
        regions.append(opp.location_country)
    if opp.location_city:
        regions.append(opp.location_city)
    data["regions"] = regions if regions else None

    # Determine remote_ok from format
    data["remote_ok"] = opp.format in ["online", "hybrid"] if opp.format else True

    return data


@router.get("")
async def list_opportunities(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in title"),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
):
    """List opportunities with optional filters."""
    query = {}
    if category:
        query["opportunity_type"] = category

    opportunities = await Opportunity.find(query).skip(skip).limit(limit).to_list()

    return {
        "items": opportunities,
        "total": await Opportunity.find(query).count(),
        "skip": skip,
        "limit": limit,
    }


@router.get("/{opportunity_id}")
async def get_opportunity(opportunity_id: str):
    """Get opportunity details by ID."""
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

    # Get host name if host_id exists
    host_name = None
    if opportunity.host_id:
        host = await Host.get(opportunity.host_id)
        if host:
            host_name = host.name

    # Transform and return data with frontend field mappings
    result = transform_opportunity_for_frontend(opportunity)
    result["host_name"] = host_name

    return result
