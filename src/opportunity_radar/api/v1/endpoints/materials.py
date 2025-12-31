"""Material generation endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from beanie import PydanticObjectId

from ....core.security import get_current_user
from ....models.user import User
from ....models.material import Material

router = APIRouter()


@router.post("/generate")
async def generate_materials(
    request: dict,
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
    # TODO: Implement AI generation service
    # For now, return a placeholder response
    return {
        "message": "Material generation not yet implemented",
        "request": request,
    }


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
        query["opportunity_id"] = PydanticObjectId(opportunity_id)

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
