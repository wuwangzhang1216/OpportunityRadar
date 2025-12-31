"""Material service for generating and managing materials."""

import logging
from typing import Dict, Any, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..ai.generator import (
    MaterialGenerator,
    ProjectContext,
    OpportunityContext as GenOpportunityContext,
    get_material_generator,
)
from ..models.batch import Batch
from ..models.opportunity import Opportunity
from ..models.material import Material
from ..repositories.material_repository import MaterialRepository
from ..schemas.material import MaterialGenerateRequest, ProjectInfo

logger = logging.getLogger(__name__)


class MaterialService:
    """Service for AI-powered material generation and management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MaterialRepository(db)
        self.generator = get_material_generator()

    async def _get_batch_with_opportunity(self, batch_id: str) -> Optional[Batch]:
        """Get batch with opportunity details loaded."""
        query = (
            select(Batch)
            .options(selectinload(Batch.opportunity))
            .where(Batch.id == batch_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def generate_materials(
        self,
        user_id: str,
        request: MaterialGenerateRequest,
    ) -> Dict[str, Any]:
        """
        Generate materials for an opportunity.

        Args:
            user_id: User ID
            request: Generation request with project info and targets

        Returns:
            Dictionary with generated materials
        """
        # Get opportunity context
        batch = await self._get_batch_with_opportunity(request.batch_id)
        if not batch:
            raise ValueError(f"Batch not found: {request.batch_id}")

        opportunity = batch.opportunity

        # Build contexts for generator
        project = ProjectContext(
            name=request.project_info.name,
            problem=request.project_info.problem,
            solution=request.project_info.solution,
            tech_stack=request.project_info.tech_stack,
            features=[],  # Could be extracted from solution
            demo_url=request.project_info.demo_url,
        )

        opp_context = GenOpportunityContext(
            title=opportunity.title,
            themes=opportunity.tags or [],
            judge_profiles=[],
            requirements=None,
        )

        # Build constraints
        constraints = {
            "highlight_demo": request.constraints.highlight_demo,
            "include_user_evidence": request.constraints.include_user_evidence,
        }
        if request.constraints.time_limit_min:
            constraints["time_limit_min"] = request.constraints.time_limit_min

        # Generate materials
        results = await self.generator.generate_all(
            project=project,
            opportunity=opp_context,
            targets=request.targets,
            constraints=constraints,
        )

        # Save materials to database and build response
        response = {
            "readme_md": None,
            "pitch_md": None,
            "demo_script_md": None,
            "qa_pred_md": None,
            "budget_json": None,
            "metadata": {
                "batch_id": request.batch_id,
                "targets": request.targets,
                "project_name": request.project_info.name,
            },
        }

        for target, result in results.items():
            # Save to database
            material = await self.repo.create_material(
                user_id=user_id,
                material_type=target,
                content=result.content,
                batch_id=request.batch_id,
                metadata_json=result.metadata,
            )

            # Map to response field
            if target == "readme":
                response["readme_md"] = result.content
            elif target.startswith("pitch"):
                response["pitch_md"] = result.content
            elif target == "demo_script":
                response["demo_script_md"] = result.content
            elif target == "qa_pred":
                response["qa_pred_md"] = result.content

            response["metadata"][f"{target}_id"] = material.id
            response["metadata"][f"{target}_version"] = material.version

        return response

    async def list_materials(
        self,
        user_id: str,
        material_type: Optional[str] = None,
        batch_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Material]:
        """List materials for a user with optional filters."""
        return await self.repo.get_by_user_id(
            user_id=user_id,
            material_type=material_type,
            batch_id=batch_id,
            skip=skip,
            limit=limit,
        )

    async def get_material(
        self,
        user_id: str,
        material_id: str,
    ) -> Optional[Material]:
        """Get a specific material by ID."""
        material = await self.repo.get(material_id)
        if material and material.user_id == user_id:
            return material
        return None

    async def delete_material(
        self,
        user_id: str,
        material_id: str,
    ) -> bool:
        """Delete a material."""
        material = await self.repo.get(material_id)
        if material and material.user_id == user_id:
            await self.repo.delete(material_id)
            return True
        return False
