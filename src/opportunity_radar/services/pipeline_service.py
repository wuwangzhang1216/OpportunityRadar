"""Pipeline service for tracking user opportunities."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.pipeline import Pipeline
from ..models.batch import Batch
from ..repositories.pipeline_repository import PipelineRepository
from ..schemas.pipeline import PipelineCreate, PipelineUpdate

logger = logging.getLogger(__name__)

# Valid pipeline stages
VALID_STAGES = ["discovered", "preparing", "submitted", "pending", "won", "lost"]


class PipelineService:
    """Service for managing user pipeline items."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PipelineRepository(db)

    async def _get_batch(self, batch_id: str) -> Optional[Batch]:
        """Get batch with timeline for deadline extraction."""
        query = (
            select(Batch)
            .options(selectinload(Batch.timeline))
            .where(Batch.id == batch_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    def _format_pipeline_response(self, pipeline: Pipeline) -> Dict[str, Any]:
        """Format pipeline item for API response."""
        opportunity = None
        if pipeline.batch and pipeline.batch.opportunity:
            opportunity = pipeline.batch.opportunity

        return {
            "id": pipeline.id,
            "user_id": pipeline.user_id,
            "batch_id": pipeline.batch_id,
            "stage": pipeline.stage,
            "eta_hours": pipeline.eta_hours,
            "deadline_at": pipeline.deadline_at,
            "notes": pipeline.notes,
            "created_at": pipeline.created_at,
            "updated_at": pipeline.updated_at,
            "opportunity_title": opportunity.title if opportunity else None,
            "opportunity_category": opportunity.category if opportunity else None,
        }

    async def create_pipeline_item(
        self,
        user_id: str,
        data: PipelineCreate,
    ) -> Dict[str, Any]:
        """
        Add an opportunity to user's pipeline.

        Args:
            user_id: User ID
            data: Pipeline creation data

        Returns:
            Created pipeline item

        Raises:
            ValueError: If batch not found or already in pipeline
        """
        # Check if batch exists
        batch = await self._get_batch(data.batch_id)
        if not batch:
            raise ValueError(f"Batch not found: {data.batch_id}")

        # Check if already in pipeline
        existing = await self.repo.get_by_user_and_batch(user_id, data.batch_id)
        if existing:
            raise ValueError("Opportunity already in pipeline")

        # Extract deadline from timeline if available
        deadline_at = None
        if batch.timeline and batch.timeline.submission_end:
            deadline_at = batch.timeline.submission_end

        # Validate stage
        stage = data.stage if data.stage in VALID_STAGES else "discovered"

        pipeline = Pipeline(
            user_id=user_id,
            batch_id=data.batch_id,
            stage=stage,
            eta_hours=data.eta_hours,
            deadline_at=deadline_at,
            notes=data.notes,
        )

        self.db.add(pipeline)
        await self.db.commit()
        await self.db.refresh(pipeline)

        # Load relationships for response
        pipeline = await self.repo.get_with_details(pipeline.id)

        return self._format_pipeline_response(pipeline)

    async def update_pipeline_item(
        self,
        user_id: str,
        pipeline_id: str,
        data: PipelineUpdate,
    ) -> Optional[Dict[str, Any]]:
        """
        Update a pipeline item.

        Args:
            user_id: User ID
            pipeline_id: Pipeline item ID
            data: Update data

        Returns:
            Updated pipeline item or None if not found
        """
        pipeline = await self.repo.get_with_details(pipeline_id)

        if not pipeline or pipeline.user_id != user_id:
            return None

        # Update fields
        if data.stage is not None and data.stage in VALID_STAGES:
            pipeline.stage = data.stage

        if data.eta_hours is not None:
            pipeline.eta_hours = data.eta_hours

        if data.notes is not None:
            pipeline.notes = data.notes

        await self.db.commit()
        await self.db.refresh(pipeline)

        # Reload with relationships
        pipeline = await self.repo.get_with_details(pipeline_id)

        return self._format_pipeline_response(pipeline)

    async def delete_pipeline_item(
        self,
        user_id: str,
        pipeline_id: str,
    ) -> bool:
        """Delete a pipeline item."""
        pipeline = await self.repo.get(pipeline_id)

        if not pipeline or pipeline.user_id != user_id:
            return False

        await self.repo.delete(pipeline_id)
        return True

    async def list_pipeline_items(
        self,
        user_id: str,
        stage: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List user's pipeline items with optional stage filter."""
        pipelines, total = await self.repo.get_by_user_id(
            user_id=user_id,
            stage=stage,
            skip=skip,
            limit=limit,
        )

        return [self._format_pipeline_response(p) for p in pipelines], total

    async def get_pipeline_stats(self, user_id: str) -> Dict[str, Any]:
        """Get pipeline statistics for a user."""
        stats = await self.repo.get_stats_by_stage(user_id)

        # Ensure all stages are present
        for stage in VALID_STAGES:
            if stage not in stats:
                stats[stage] = 0

        total = sum(stats.values())

        return {
            "total": total,
            "by_stage": stats,
        }

    async def get_upcoming_deadlines(
        self,
        user_id: str,
        days_ahead: int = 7,
    ) -> List[Dict[str, Any]]:
        """Get pipeline items with upcoming deadlines."""
        pipelines = await self.repo.get_upcoming_deadlines(user_id, days_ahead)

        return [
            {
                **self._format_pipeline_response(p),
                "days_until_deadline": (p.deadline_at - datetime.utcnow()).days
                if p.deadline_at
                else None,
            }
            for p in pipelines
        ]

    async def move_to_stage(
        self,
        user_id: str,
        pipeline_id: str,
        stage: str,
    ) -> Optional[Dict[str, Any]]:
        """Quick method to move pipeline item to a new stage."""
        if stage not in VALID_STAGES:
            raise ValueError(f"Invalid stage: {stage}")

        return await self.update_pipeline_item(
            user_id=user_id,
            pipeline_id=pipeline_id,
            data=PipelineUpdate(stage=stage),
        )
