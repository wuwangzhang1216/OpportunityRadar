"""Data export API endpoints."""

from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from beanie import PydanticObjectId

from ....models.user import User
from ....models.pipeline import Pipeline
from ....services.export_service import get_export_service
from ....core.security import get_current_user

router = APIRouter()

ExportFormat = Literal["json", "csv"]


@router.get("/user-data")
async def export_user_data(
    format: ExportFormat = Query("json", description="Export format: json or csv"),
    include_profile: bool = Query(True, description="Include profile data"),
    include_matches: bool = Query(True, description="Include match history"),
    include_pipelines: bool = Query(True, description="Include pipeline data"),
    include_materials: bool = Query(True, description="Include generated materials"),
    current_user: User = Depends(get_current_user),
):
    """
    Export all user data.

    Generates a downloadable file containing:
    - User account information
    - Profile data
    - Match history with opportunities
    - Pipeline data with opportunities
    - Generated materials

    Supports JSON and CSV formats.
    """
    service = get_export_service()

    content, filename = await service.export_user_data(
        user=current_user,
        include_profile=include_profile,
        include_matches=include_matches,
        include_pipelines=include_pipelines,
        include_materials=include_materials,
        format=format,
    )

    media_type = "application/json" if format == "json" else "text/csv"

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/opportunities")
async def export_opportunities(
    opportunity_ids: str = Query(..., description="Comma-separated opportunity IDs"),
    format: ExportFormat = Query("json", description="Export format: json or csv"),
    current_user: User = Depends(get_current_user),
):
    """
    Export a list of opportunities.

    Provide comma-separated opportunity IDs to export.
    """
    service = get_export_service()

    # Parse opportunity IDs
    try:
        ids = [
            PydanticObjectId(id.strip())
            for id in opportunity_ids.split(",")
            if id.strip()
        ]
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid opportunity ID format",
        )

    if not ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No opportunity IDs provided",
        )

    content, filename = await service.export_opportunities(ids, format)

    media_type = "application/json" if format == "json" else "text/csv"

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/pipeline/{pipeline_id}")
async def export_pipeline_opportunities(
    pipeline_id: str,
    format: ExportFormat = Query("json", description="Export format: json or csv"),
    current_user: User = Depends(get_current_user),
):
    """
    Export all opportunities in a pipeline.

    Returns a downloadable file with all opportunity details from the pipeline.
    """
    service = get_export_service()

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
            detail="Not authorized to export this pipeline",
        )

    try:
        content, filename = await service.export_pipeline_opportunities(
            pipeline_id=pipeline.id, format=format
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    media_type = "application/json" if format == "json" else "text/csv"

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/matches")
async def export_matches(
    format: ExportFormat = Query("json", description="Export format: json or csv"),
    status_filter: Optional[str] = Query(None, description="Filter by match status"),
    current_user: User = Depends(get_current_user),
):
    """
    Export user's match history.

    Returns a list of all matched opportunities with scores and status.
    """
    service = get_export_service()

    content, filename = await service.export_user_data(
        user=current_user,
        include_profile=False,
        include_matches=True,
        include_pipelines=False,
        include_materials=False,
        format=format,
    )

    media_type = "application/json" if format == "json" else "text/csv"

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="matches_{filename.split("_")[-1]}"',
        },
    )
