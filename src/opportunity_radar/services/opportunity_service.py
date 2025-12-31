"""Service layer for Opportunity operations."""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.opportunity import Opportunity
from ..repositories.opportunity_repository import OpportunityRepository
from ..scrapers.base import RawOpportunity, ScraperResult
from ..scrapers.normalizer import DataNormalizer
from ..schemas.opportunity import OpportunityResponse, OpportunityListResponse

logger = logging.getLogger(__name__)


class OpportunityService:
    """Service for opportunity-related operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = OpportunityRepository(db)
        self.normalizer = DataNormalizer()

    async def get_opportunity(self, opportunity_id: str) -> Optional[OpportunityResponse]:
        """Get a single opportunity by ID."""
        opportunity = await self.repository.get_with_batches(opportunity_id)
        if not opportunity:
            return None
        return self._to_response(opportunity)

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
    ) -> OpportunityListResponse:
        """List opportunities with filters."""
        opportunities, total = await self.repository.list_opportunities(
            skip=skip,
            limit=limit,
            category=category,
            source=source,
            status=status,
            region=region,
            remote_ok=remote_ok,
            deadline_before=deadline_before,
            deadline_after=deadline_after,
            search_query=search_query,
            sort_by=sort_by,
        )

        return OpportunityListResponse(
            items=[self._to_response(opp) for opp in opportunities],
            total=total,
            limit=limit,
            offset=skip,
        )

    async def get_upcoming_opportunities(self, limit: int = 20) -> List[OpportunityResponse]:
        """Get upcoming opportunities."""
        opportunities = await self.repository.get_upcoming(limit)
        return [self._to_response(opp) for opp in opportunities]

    async def ingest_scraper_result(self, result: ScraperResult) -> Dict:
        """
        Ingest scraped opportunities into the database.
        Returns statistics about the ingestion.
        """
        stats = {
            "source": result.source,
            "total_scraped": len(result.opportunities),
            "inserted": 0,
            "updated": 0,
            "failed": 0,
            "errors": [],
        }

        for raw_opp in result.opportunities:
            try:
                await self.upsert_raw_opportunity(raw_opp)

                # Check if it was an insert or update
                existing = await self.repository.get_by_external_id(
                    raw_opp.source, raw_opp.external_id
                )
                if existing and existing.created_at == existing.updated_at:
                    stats["inserted"] += 1
                else:
                    stats["updated"] += 1

            except Exception as e:
                stats["failed"] += 1
                stats["errors"].append(f"{raw_opp.external_id}: {str(e)}")
                logger.error(f"Failed to ingest {raw_opp.external_id}: {e}")

        await self.db.commit()

        logger.info(
            f"Ingestion complete for {result.source}: "
            f"{stats['inserted']} inserted, {stats['updated']} updated, "
            f"{stats['failed']} failed"
        )

        return stats

    async def upsert_raw_opportunity(self, raw: RawOpportunity) -> Opportunity:
        """Normalize and upsert a raw opportunity."""
        # Normalize the raw data
        opp_data, batch_data, timeline_data, prizes_data = self.normalizer.normalize(raw)

        # Prepare host data if available
        host_data = None
        if raw.host_name:
            host_data = {
                "name": raw.host_name,
                "website": raw.host_url,
                "type": "company",
            }

        # Upsert to database
        opportunity = await self.repository.upsert_opportunity(
            opportunity_data=opp_data,
            batch_data=batch_data,
            timeline_data=timeline_data,
            prizes_data=prizes_data,
            host_data=host_data,
        )

        return opportunity

    async def search_opportunities(
        self,
        query: str,
        limit: int = 20,
    ) -> List[OpportunityResponse]:
        """Text search for opportunities."""
        opportunities, _ = await self.repository.list_opportunities(
            search_query=query,
            limit=limit,
        )
        return [self._to_response(opp) for opp in opportunities]

    async def get_statistics(self) -> Dict:
        """Get opportunity statistics."""
        return await self.repository.get_statistics()

    def _to_response(self, opportunity: Opportunity) -> OpportunityResponse:
        """Convert Opportunity model to response schema."""
        from ..schemas.opportunity import (
            OpportunityResponse,
            HostSchema,
            BatchSchema,
            TimelineSchema,
            PrizeSchema,
        )

        # Build host schema
        host_schema = None
        if opportunity.host:
            host_schema = HostSchema(
                id=opportunity.host.id,
                name=opportunity.host.name,
                type=opportunity.host.type,
                country=opportunity.host.country,
                website=opportunity.host.website,
                reputation_score=opportunity.host.reputation_score,
            )

        # Build current batch schema (most recent)
        current_batch = None
        if opportunity.batches:
            batch = opportunity.batches[0]  # Assuming sorted by date

            timeline_schema = None
            if batch.timeline:
                timeline_schema = TimelineSchema(
                    registration_opens_at=batch.timeline.registration_opens_at,
                    registration_closes_at=batch.timeline.registration_closes_at,
                    event_starts_at=batch.timeline.event_starts_at,
                    event_ends_at=batch.timeline.event_ends_at,
                    submission_deadline=batch.timeline.submission_deadline,
                    demo_at=batch.timeline.demo_at,
                    results_at=batch.timeline.results_at,
                    timezone=batch.timeline.timezone,
                )

            prizes_schema = []
            if batch.prizes:
                for prize in batch.prizes:
                    prizes_schema.append(
                        PrizeSchema(
                            id=prize.id,
                            prize_type=prize.prize_type,
                            name=prize.name,
                            amount=prize.amount,
                            currency=prize.currency,
                            benefits=prize.benefits or [],
                        )
                    )

            current_batch = BatchSchema(
                id=batch.id,
                opportunity_id=batch.opportunity_id,
                year=batch.year,
                season=batch.season,
                remote_ok=batch.remote_ok,
                regions=batch.regions or [],
                team_min=batch.team_min,
                team_max=batch.team_max,
                student_only=batch.student_only,
                startup_stages=batch.startup_stages or [],
                sponsors=batch.sponsors or [],
                status=batch.status,
                timeline=timeline_schema,
                prizes=prizes_schema,
            )

        return OpportunityResponse(
            id=opportunity.id,
            source=opportunity.source,
            category=opportunity.category,
            title=opportunity.title,
            description=opportunity.description,
            tags=opportunity.tags or [],
            industry=opportunity.industry or [],
            tech_stack=opportunity.tech_stack or [],
            locale=opportunity.locale or [],
            url=opportunity.url,
            image_url=opportunity.image_url,
            credibility_score=opportunity.credibility_score,
            created_at=opportunity.created_at,
            updated_at=opportunity.updated_at,
            host=host_schema,
            current_batch=current_batch,
        )


# Convenience function for running scraper and ingesting results
async def run_scraper_and_ingest(
    db: AsyncSession,
    scraper_name: str,
    max_pages: int = 10,
) -> Dict:
    """Run a scraper and ingest results into database."""
    from ..scrapers.scheduler import scraper_manager

    # Run scraper
    result = await scraper_manager.run_scraper(scraper_name, max_pages=max_pages)

    if not result.success:
        return {
            "status": "failed",
            "error": result.error_message,
            "source": scraper_name,
        }

    # Ingest results
    service = OpportunityService(db)
    stats = await service.ingest_scraper_result(result)

    return {
        "status": "success",
        "source": scraper_name,
        **stats,
    }
