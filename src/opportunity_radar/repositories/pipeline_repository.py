"""Pipeline repository for data access."""

from typing import List, Optional, Tuple

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from ..models.pipeline import Pipeline
from ..models.batch import Batch
from ..models.opportunity import Opportunity


class PipelineRepository(BaseRepository[Pipeline]):
    """Repository for Pipeline CRUD operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(Pipeline, db)

    async def get_by_user_id(
        self,
        user_id: str,
        stage: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Pipeline], int]:
        """Get pipeline items for a user with optional stage filter."""
        conditions = [Pipeline.user_id == user_id]

        if stage:
            conditions.append(Pipeline.stage == stage)

        # Count query
        count_query = select(func.count()).select_from(Pipeline).where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        # Data query with relationships
        query = (
            select(Pipeline)
            .options(
                selectinload(Pipeline.batch).selectinload(Batch.opportunity),
                selectinload(Pipeline.batch).selectinload(Batch.timeline),
            )
            .where(and_(*conditions))
            .order_by(Pipeline.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_by_user_and_batch(
        self,
        user_id: str,
        batch_id: str,
    ) -> Optional[Pipeline]:
        """Get a specific pipeline item for user and batch."""
        query = (
            select(Pipeline)
            .options(
                selectinload(Pipeline.batch).selectinload(Batch.opportunity),
            )
            .where(
                and_(
                    Pipeline.user_id == user_id,
                    Pipeline.batch_id == batch_id,
                )
            )
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_with_details(self, pipeline_id: str) -> Optional[Pipeline]:
        """Get pipeline item with batch and opportunity details."""
        query = (
            select(Pipeline)
            .options(
                selectinload(Pipeline.batch).selectinload(Batch.opportunity),
                selectinload(Pipeline.batch).selectinload(Batch.timeline),
            )
            .where(Pipeline.id == pipeline_id)
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_upcoming_deadlines(
        self,
        user_id: str,
        days_ahead: int = 7,
    ) -> List[Pipeline]:
        """Get pipeline items with deadlines in the next N days."""
        from datetime import datetime, timedelta

        now = datetime.utcnow()
        deadline_cutoff = now + timedelta(days=days_ahead)

        query = (
            select(Pipeline)
            .options(
                selectinload(Pipeline.batch).selectinload(Batch.opportunity),
                selectinload(Pipeline.batch).selectinload(Batch.timeline),
            )
            .where(
                and_(
                    Pipeline.user_id == user_id,
                    Pipeline.deadline_at != None,
                    Pipeline.deadline_at <= deadline_cutoff,
                    Pipeline.deadline_at >= now,
                    Pipeline.stage.not_in(["won", "lost"]),
                )
            )
            .order_by(Pipeline.deadline_at.asc())
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_stats_by_stage(self, user_id: str) -> dict:
        """Get count of pipeline items by stage."""
        query = (
            select(Pipeline.stage, func.count(Pipeline.id))
            .where(Pipeline.user_id == user_id)
            .group_by(Pipeline.stage)
        )

        result = await self.db.execute(query)
        rows = result.all()

        return {row[0]: row[1] for row in rows}
