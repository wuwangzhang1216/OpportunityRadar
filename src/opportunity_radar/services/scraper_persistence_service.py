"""Service for persisting scraped opportunities to MongoDB."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from ..models.opportunity import Opportunity
from ..models.scraper_run import ScraperRun
from ..scrapers.base import RawOpportunity, ScraperResult, ScraperStatus

logger = logging.getLogger(__name__)

# Scraper to opportunity type mapping
TYPE_MAPPING = {
    "devpost": "hackathon",
    "mlh": "hackathon",
    "ethglobal": "hackathon",
    "kaggle": "competition",
    "hackerearth": "hackathon",
    "grants_gov": "grant",
    "sbir": "grant",
    "eu_horizon": "grant",
    "innovate_uk": "grant",
    "hackerone": "bounty",
    "accelerators": "accelerator",
    "opensource_grants": "grant",
}


class ScraperPersistenceService:
    """Service for persisting scraped data to MongoDB."""

    async def persist_scraper_result(
        self,
        result: ScraperResult,
        triggered_by: Optional[str] = None,
    ) -> Dict:
        """
        Persist scraped opportunities to the database and create ScraperRun record.

        Args:
            result: The scraper result containing opportunities
            triggered_by: Optional user ID if manually triggered

        Returns:
            Statistics about the persistence operation
        """
        # Create ScraperRun record
        scraper_run = ScraperRun(
            scraper_name=result.source,
            status="running",
            opportunities_found=len(result.opportunities),
        )
        await scraper_run.insert()

        stats = {
            "source": result.source,
            "scraper_run_id": str(scraper_run.id),
            "total_scraped": len(result.opportunities),
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "errors": [],
        }

        try:
            for raw_opp in result.opportunities:
                try:
                    await self._upsert_opportunity(raw_opp, result.source, stats)
                except Exception as e:
                    stats["skipped"] += 1
                    error_msg = f"{raw_opp.external_id}: {str(e)[:100]}"
                    stats["errors"].append(error_msg)
                    logger.error(f"Failed to persist {raw_opp.external_id}: {e}")

            # Update ScraperRun with final stats
            scraper_run.opportunities_created = stats["inserted"]
            scraper_run.opportunities_updated = stats["updated"]
            scraper_run.errors = stats["errors"][:20]  # Keep first 20 errors

            if stats["errors"]:
                if stats["inserted"] > 0 or stats["updated"] > 0:
                    scraper_run.mark_partial()
                else:
                    scraper_run.mark_failed()
            else:
                scraper_run.mark_success()

            await scraper_run.save()

            logger.info(
                f"Persistence complete for {result.source}: "
                f"{stats['inserted']} inserted, {stats['updated']} updated, "
                f"{stats['skipped']} skipped"
            )

            # Generate embeddings for new opportunities
            if stats["inserted"] > 0:
                try:
                    from .opportunity_embedding_service import get_opportunity_embedding_service
                    embedding_service = get_opportunity_embedding_service()
                    embedding_stats = await embedding_service.generate_embeddings_batch(
                        only_missing=True,
                        batch_size=50,
                    )
                    stats["embeddings_generated"] = embedding_stats.get("success", 0)
                    logger.info(f"Generated {stats['embeddings_generated']} embeddings for new opportunities")
                except Exception as e:
                    logger.warning(f"Failed to generate embeddings: {e}")
                    stats["embedding_error"] = str(e)

        except Exception as e:
            scraper_run.mark_failed(str(e))
            await scraper_run.save()
            logger.error(f"Persistence failed for {result.source}: {e}")
            stats["errors"].append(str(e))

        return stats

    async def _upsert_opportunity(
        self,
        raw_opp: RawOpportunity,
        source: str,
        stats: Dict,
    ) -> Opportunity:
        """Upsert a single opportunity to the database."""
        # Check if already exists
        existing = await Opportunity.find_one(
            Opportunity.external_id == raw_opp.external_id
        )

        if existing:
            # Update existing record
            existing.title = raw_opp.title
            existing.description = raw_opp.description
            existing.short_description = (
                raw_opp.description[:200] if raw_opp.description else None
            )
            existing.total_prize_value = raw_opp.total_prize_amount
            existing.themes = raw_opp.themes or []
            existing.technologies = raw_opp.tech_stack or []
            existing.website_url = raw_opp.url
            existing.logo_url = raw_opp.image_url
            existing.format = "online" if raw_opp.is_online else "in-person"
            existing.location_city = raw_opp.location
            existing.team_size_min = raw_opp.team_min
            existing.team_size_max = raw_opp.team_max
            existing.updated_at = datetime.utcnow()
            await existing.save()
            stats["updated"] += 1
            return existing
        else:
            # Create new record
            opp = Opportunity(
                external_id=raw_opp.external_id,
                title=raw_opp.title,
                description=raw_opp.description,
                short_description=(
                    raw_opp.description[:200] if raw_opp.description else None
                ),
                opportunity_type=TYPE_MAPPING.get(source, "other"),
                website_url=raw_opp.url,
                source_url=raw_opp.url,
                logo_url=raw_opp.image_url,
                banner_url=raw_opp.image_url,
                themes=raw_opp.themes or [],
                technologies=raw_opp.tech_stack or [],
                total_prize_value=raw_opp.total_prize_amount,
                location_city=raw_opp.location,
                format="online" if raw_opp.is_online else "in-person",
                team_size_min=raw_opp.team_min,
                team_size_max=raw_opp.team_max,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            await opp.insert()
            stats["inserted"] += 1
            return opp


# Singleton instance
_service: Optional[ScraperPersistenceService] = None


def get_scraper_persistence_service() -> ScraperPersistenceService:
    """Get or create the scraper persistence service singleton."""
    global _service
    if _service is None:
        _service = ScraperPersistenceService()
    return _service
