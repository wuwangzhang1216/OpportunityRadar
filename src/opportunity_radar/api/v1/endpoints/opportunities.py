"""Opportunities API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Query, HTTPException, status
from beanie import PydanticObjectId

from ....models.opportunity import Opportunity, Host

router = APIRouter()


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

    return opportunity
