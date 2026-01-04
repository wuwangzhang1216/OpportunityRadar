"""Material generation endpoints."""

import logging
from typing import Optional, List

from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from beanie import PydanticObjectId

from ....core.security import get_current_user
from ....models.user import User
from ....models.material import Material
from ....models.opportunity import Opportunity
from ....schemas.material import (
    MaterialGenerateRequest,
    MaterialResponse,
    GenerationError,
)
from ....ai.generator import (
    get_material_generator,
    ProjectContext,
    OpportunityContext,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def generate_materials(
    request: MaterialGenerateRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Generate materials for an opportunity using AI.

    Targets can include:
    - readme: Project README.md
    - pitch_1min, pitch_3min, pitch_5min: Pitch scripts
    - demo_script: Live demo script
    - qa_pred: Predicted Q&A for judges
    """
    logger.info(
        f"Material generation requested by user={current_user.id}, "
        f"targets={request.targets}"
    )

    # Get opportunity context (optional) with authorization check
    opportunity = None
    opp_context = OpportunityContext(title="General Project", themes=[])

    if request.opportunity_id:
        try:
            opportunity = await Opportunity.get(PydanticObjectId(request.opportunity_id))
        except InvalidId:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid opportunity ID format",
            )
        except Exception as e:
            logger.error(f"Database error fetching opportunity: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to validate opportunity",
            )

        if not opportunity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Opportunity not found",
            )

        # Check if opportunity is active (authorization)
        if not opportunity.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot generate materials for inactive opportunity",
            )

        opp_context = OpportunityContext(
            title=opportunity.title,
            themes=opportunity.tags or [],
        )

    # Build project context from request
    project = ProjectContext(
        name=request.project_info.name,
        problem=request.project_info.problem,
        solution=request.project_info.solution,
        tech_stack=request.project_info.tech_stack,
        demo_url=request.project_info.demo_url,
    )

    # Get generator and generate materials
    generator = get_material_generator()

    try:
        results = await generator.generate_all(
            project=project,
            opportunity=opp_context,
            targets=request.targets,
            constraints={
                "highlight_demo": request.constraints.highlight_demo,
                "include_user_evidence": request.constraints.include_user_evidence,
                "time_limit_min": request.constraints.time_limit_min,
            } if request.constraints else None,
        )
    except Exception as e:
        logger.error(f"Material generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI generation service temporarily unavailable",
        )

    # Build response and save materials to MongoDB
    response_data = {
        "readme_md": None,
        "pitch_md": None,
        "demo_script_md": None,
        "qa_pred_md": None,
        "metadata": {"targets": request.targets, "project_name": request.project_info.name},
    }
    errors: List[GenerationError] = []

    for target, result in results.items():
        # Check if generation had an error - track partial failures
        if result.metadata and result.metadata.get("error"):
            error_msg = result.metadata.get("error", "Unknown generation error")
            logger.warning(f"Generation error for {target}: {error_msg}")
            errors.append(GenerationError(target=target, error=error_msg))
            continue

        # Save to MongoDB
        material = Material(
            user_id=current_user.id,
            opportunity_id=opportunity.id if opportunity else None,
            material_type=target,
            content=result.content,
            metadata=result.metadata or {},
            model_used="gpt-4o-mini",
        )
        await material.insert()

        # Map to response fields
        if target == "readme":
            response_data["readme_md"] = result.content
        elif target.startswith("pitch"):
            response_data["pitch_md"] = result.content
        elif target == "demo_script":
            response_data["demo_script_md"] = result.content
        elif target == "qa_pred":
            response_data["qa_pred_md"] = result.content

        response_data["metadata"][f"{target}_id"] = str(material.id)

    logger.info(f"Material generation completed for user={current_user.id}")
    return MaterialResponse(**response_data, errors=errors)


@router.get("")
async def list_materials(
    material_type: Optional[str] = Query(None, description="Filter by type"),
    opportunity_id: Optional[str] = Query(None, description="Filter by opportunity"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """List generated materials for current user."""
    query = {"user_id": current_user.id}
    if material_type:
        query["material_type"] = material_type
    if opportunity_id:
        try:
            query["opportunity_id"] = PydanticObjectId(opportunity_id)
        except InvalidId:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid opportunity ID format",
            )

    materials = await Material.find(query).skip(skip).limit(limit).to_list()

    return {
        "items": [
            {
                "id": str(m.id),
                "user_id": str(m.user_id),
                "opportunity_id": str(m.opportunity_id) if m.opportunity_id else None,
                "material_type": m.material_type,
                "content": m.content[:500] + "..." if len(m.content) > 500 else m.content,
                "version": m.version,
                "metadata": m.metadata or {},
                "created_at": m.created_at,
            }
            for m in materials
        ],
        "count": len(materials),
    }


@router.get("/{material_id}")
async def get_material(
    material_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get specific generated material with full content."""
    try:
        material = await Material.get(PydanticObjectId(material_id))
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid material ID format",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found",
        )

    if not material or material.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found",
        )

    return {
        "id": str(material.id),
        "user_id": str(material.user_id),
        "opportunity_id": str(material.opportunity_id) if material.opportunity_id else None,
        "material_type": material.material_type,
        "content": material.content,
        "version": material.version,
        "metadata": material.metadata or {},
        "created_at": material.created_at,
    }


@router.delete("/{material_id}")
async def delete_material(
    material_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a generated material."""
    try:
        material = await Material.get(PydanticObjectId(material_id))
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid material ID format",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found",
        )

    if not material or material.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found",
        )

    await material.delete()

    return {"message": "Material deleted", "material_id": material_id}
