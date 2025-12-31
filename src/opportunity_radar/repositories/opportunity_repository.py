"""Repository for Opportunity and related models."""

import logging
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import uuid4

from sqlalchemy import and_, or_, select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from ..models.opportunity import Opportunity
from ..models.batch import Batch
from ..models.timeline import Timeline
from ..models.prize import Prize
from ..models.host import Host

logger = logging.getLogger(__name__)


class OpportunityRepository(BaseRepository[Opportunity]):
    """Repository for Opportunity CRUD and queries."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Opportunity)

    async def get_with_batches(self, id: str) -> Optional[Opportunity]:
        """Get opportunity with all batches loaded."""
        result = await self.db.execute(
            select(Opportunity)
            .options(
                selectinload(Opportunity.batches).selectinload(Batch.timeline),
                selectinload(Opportunity.batches).selectinload(Batch.prizes),
                selectinload(Opportunity.host),
            )
            .where(Opportunity.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_external_id(self, source: str, external_id: str) -> Optional[Opportunity]:
        """Get opportunity by source and external ID."""
        result = await self.db.execute(
            select(Opportunity).where(
                and_(
                    Opportunity.source == source,
                    Opportunity.external_id == external_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_opportunities(
        self,
        skip: int = 0,
        limit: int = 20,
        category: Optional[str] = None,
        source: Optional[str] = None,
        status: Optional[str] = None,
        region: Optional[str] = None,
        remote_ok: Optional[bool] = None,
        deadline_before: Optional[datetime] = None,
        deadline_after: Optional[datetime] = None,
        search_query: Optional[str] = None,
        sort_by: str = "freshness",
    ) -> Tuple[List[Opportunity], int]:
        """List opportunities with filters and pagination."""
        # Base query with eager loading
        query = (
            select(Opportunity)
            .options(
                selectinload(Opportunity.batches).selectinload(Batch.timeline),
                selectinload(Opportunity.host),
            )
        )

        # Build filter conditions
        conditions = []

        if category:
            conditions.append(Opportunity.category == category)

        if source:
            conditions.append(Opportunity.source == source)

        if search_query:
            search_pattern = f"%{search_query}%"
            conditions.append(
                or_(
                    Opportunity.title.ilike(search_pattern),
                    Opportunity.description.ilike(search_pattern),
                )
            )

        # Apply conditions
        if conditions:
            query = query.where(and_(*conditions))

        # Count total before pagination
        count_query = select(func.count()).select_from(Opportunity)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Sorting
        if sort_by == "freshness":
            query = query.order_by(desc(Opportunity.created_at))
        elif sort_by == "deadline":
            # Join with batch/timeline for deadline sorting
            query = query.join(Opportunity.batches).join(Batch.timeline)
            query = query.order_by(Timeline.submission_deadline.asc().nullslast())
        elif sort_by == "title":
            query = query.order_by(Opportunity.title)

        # Pagination
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        opportunities = list(result.scalars().unique().all())

        return opportunities, total

    async def upsert_opportunity(
        self,
        opportunity_data: dict,
        batch_data: dict,
        timeline_data: dict,
        prizes_data: List[dict],
        host_data: Optional[dict] = None,
    ) -> Opportunity:
        """
        Insert or update an opportunity with its batch, timeline, and prizes.
        Uses source + external_id as unique key.
        """
        source = opportunity_data["source"]
        external_id = opportunity_data["external_id"]

        # Check if exists
        existing = await self.get_by_external_id(source, external_id)

        if existing:
            # Update existing opportunity
            for field, value in opportunity_data.items():
                if field not in ["id", "created_at"] and hasattr(existing, field):
                    setattr(existing, field, value)

            # Update or create batch
            if existing.batches:
                batch = existing.batches[0]
                for field, value in batch_data.items():
                    if field not in ["id", "opportunity_id", "created_at"] and hasattr(batch, field):
                        setattr(batch, field, value)

                # Update timeline
                if batch.timeline:
                    for field, value in timeline_data.items():
                        if field not in ["id", "batch_id", "created_at"] and hasattr(batch.timeline, field):
                            setattr(batch.timeline, field, value)
            else:
                # Create new batch
                await self._create_batch(existing.id, batch_data, timeline_data, prizes_data)

            await self.db.flush()
            await self.db.refresh(existing)
            return existing

        else:
            # Handle host
            host_id = None
            if host_data and host_data.get("name"):
                host = await self._get_or_create_host(host_data)
                host_id = host.id

            # Create new opportunity
            opportunity_data["id"] = str(uuid4())
            opportunity_data["host_id"] = host_id
            opportunity = Opportunity(**opportunity_data)
            self.db.add(opportunity)
            await self.db.flush()

            # Create batch, timeline, prizes
            await self._create_batch(opportunity.id, batch_data, timeline_data, prizes_data)

            await self.db.refresh(opportunity)
            return opportunity

    async def _create_batch(
        self,
        opportunity_id: str,
        batch_data: dict,
        timeline_data: dict,
        prizes_data: List[dict],
    ) -> Batch:
        """Create a batch with timeline and prizes."""
        batch_data["id"] = str(uuid4())
        batch_data["opportunity_id"] = opportunity_id
        batch = Batch(**batch_data)
        self.db.add(batch)
        await self.db.flush()

        # Create timeline
        timeline_data["id"] = str(uuid4())
        timeline_data["batch_id"] = batch.id
        timeline = Timeline(**timeline_data)
        self.db.add(timeline)

        # Create prizes
        for prize_data in prizes_data:
            prize_data["id"] = str(uuid4())
            prize_data["batch_id"] = batch.id
            prize = Prize(**prize_data)
            self.db.add(prize)

        await self.db.flush()
        return batch

    async def _get_or_create_host(self, host_data: dict) -> Host:
        """Get or create a host."""
        result = await self.db.execute(
            select(Host).where(Host.name == host_data["name"])
        )
        host = result.scalar_one_or_none()

        if not host:
            host_data["id"] = str(uuid4())
            host_data["type"] = host_data.get("type", "company")
            host = Host(**host_data)
            self.db.add(host)
            await self.db.flush()

        return host

    async def get_by_source(self, source: str, limit: int = 100) -> List[Opportunity]:
        """Get all opportunities from a specific source."""
        result = await self.db.execute(
            select(Opportunity)
            .where(Opportunity.source == source)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_upcoming(self, limit: int = 20) -> List[Opportunity]:
        """Get upcoming opportunities (deadline in future)."""
        now = datetime.utcnow()
        result = await self.db.execute(
            select(Opportunity)
            .options(
                selectinload(Opportunity.batches).selectinload(Batch.timeline),
            )
            .join(Opportunity.batches)
            .join(Batch.timeline)
            .where(
                or_(
                    Timeline.submission_deadline > now,
                    Timeline.submission_deadline.is_(None),
                )
            )
            .order_by(Timeline.submission_deadline.asc().nullslast())
            .limit(limit)
        )
        return list(result.scalars().unique().all())

    async def search_vector(
        self,
        embedding: List[float],
        limit: int = 20,
        threshold: float = 0.7,
    ) -> List[Tuple[Opportunity, float]]:
        """
        Search opportunities using vector similarity.
        Returns list of (opportunity, similarity_score) tuples.
        """
        # Using pgvector's cosine distance operator
        # Note: cosine_distance = 1 - cosine_similarity
        from pgvector.sqlalchemy import Vector

        result = await self.db.execute(
            select(
                Opportunity,
                (1 - Opportunity.embedding.cosine_distance(embedding)).label("similarity"),
            )
            .where(Opportunity.embedding.isnot(None))
            .order_by(Opportunity.embedding.cosine_distance(embedding))
            .limit(limit)
        )

        rows = result.all()
        return [(row[0], row[1]) for row in rows if row[1] >= threshold]

    async def get_statistics(self) -> dict:
        """Get statistics about opportunities."""
        total = await self.count()

        # Count by source
        source_counts = await self.db.execute(
            select(Opportunity.source, func.count(Opportunity.id))
            .group_by(Opportunity.source)
        )
        by_source = {row[0]: row[1] for row in source_counts.all()}

        # Count by category
        category_counts = await self.db.execute(
            select(Opportunity.category, func.count(Opportunity.id))
            .group_by(Opportunity.category)
        )
        by_category = {row[0]: row[1] for row in category_counts.all()}

        return {
            "total": total,
            "by_source": by_source,
            "by_category": by_category,
        }
