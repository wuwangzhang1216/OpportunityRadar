"""Pipeline endpoints."""

from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from beanie import PydanticObjectId

from ....core.security import get_current_user
from ....models.user import User
from ....models.pipeline import Pipeline

router = APIRouter()

VALID_STAGES = ["discovered", "preparing", "submitted", "pending", "won", "lost"]


@router.get("")
async def list_pipelines(
    stage: Optional[str] = Query(None, description="Filter by stage"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """
    Get user's pipeline items.

    Stages: discovered, preparing, submitted, pending, won, lost
    """
    query = {"user_id": current_user.id}
    if stage:
        query["status"] = stage

    items = await Pipeline.find(query).skip(skip).limit(limit).to_list()
    total = await Pipeline.find(query).count()

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": skip,
    }


@router.get("/stats")
async def get_pipeline_stats(
    current_user: User = Depends(get_current_user),
):
    """Get pipeline statistics for current user."""
    stats = {}
    for stage in VALID_STAGES:
        count = await Pipeline.find(
            Pipeline.user_id == current_user.id,
            Pipeline.status == stage
        ).count()
        stats[stage] = count

    total = sum(stats.values())

    return {
        "total": total,
        "by_stage": stats,
    }


@router.get("/deadlines")
async def get_upcoming_deadlines(
    days: int = Query(7, ge=1, le=30, description="Days to look ahead"),
    current_user: User = Depends(get_current_user),
):
    """Get pipeline items with upcoming deadlines."""
    now = datetime.utcnow()
    deadline = now + timedelta(days=days)

    items = await Pipeline.find(
        Pipeline.user_id == current_user.id,
        Pipeline.deadline != None,
        Pipeline.deadline <= deadline,
        Pipeline.deadline >= now,
    ).sort(Pipeline.deadline).to_list()

    return {"items": items, "count": len(items)}


@router.post("")
async def create_pipeline(
    pipeline_data: dict,
    current_user: User = Depends(get_current_user),
):
    """Add opportunity to pipeline."""
    opportunity_id = pipeline_data.get("opportunity_id")
    if not opportunity_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="opportunity_id is required",
        )

    # Check if already in pipeline
    existing = await Pipeline.find_one(
        Pipeline.user_id == current_user.id,
        Pipeline.opportunity_id == PydanticObjectId(opportunity_id)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Opportunity already in pipeline",
        )

    pipeline = Pipeline(
        user_id=current_user.id,
        opportunity_id=PydanticObjectId(opportunity_id),
        status=pipeline_data.get("stage", "discovered"),
        notes=pipeline_data.get("notes"),
    )
    await pipeline.insert()

    return pipeline


@router.patch("/{pipeline_id}")
async def update_pipeline(
    pipeline_id: str,
    pipeline_data: dict,
    current_user: User = Depends(get_current_user),
):
    """Update pipeline item (stage, notes, deadline)."""
    try:
        pipeline = await Pipeline.get(PydanticObjectId(pipeline_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline item not found",
        )

    if not pipeline or pipeline.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline item not found",
        )

    for key, value in pipeline_data.items():
        if hasattr(pipeline, key) and key not in ["id", "user_id", "opportunity_id", "created_at"]:
            setattr(pipeline, key, value)

    pipeline.updated_at = datetime.utcnow()
    await pipeline.save()

    return pipeline


@router.post("/{pipeline_id}/stage/{stage}")
async def move_to_stage(
    pipeline_id: str,
    stage: str,
    current_user: User = Depends(get_current_user),
):
    """Quick endpoint to move pipeline item to a specific stage."""
    if stage not in VALID_STAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid stage. Must be one of: {', '.join(VALID_STAGES)}",
        )

    try:
        pipeline = await Pipeline.get(PydanticObjectId(pipeline_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline item not found",
        )

    if not pipeline or pipeline.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline item not found",
        )

    pipeline.status = stage
    pipeline.updated_at = datetime.utcnow()
    await pipeline.save()

    return pipeline


@router.delete("/{pipeline_id}")
async def delete_pipeline(
    pipeline_id: str,
    current_user: User = Depends(get_current_user),
):
    """Remove item from pipeline."""
    try:
        pipeline = await Pipeline.get(PydanticObjectId(pipeline_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline item not found",
        )

    if not pipeline or pipeline.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline item not found",
        )

    await pipeline.delete()

    return {"message": "Pipeline item deleted", "pipeline_id": pipeline_id}
