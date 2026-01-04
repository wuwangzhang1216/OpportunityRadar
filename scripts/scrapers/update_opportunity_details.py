"""Script to update existing opportunities with detailed information from scrapers."""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def update_opportunities_for_source(source: str, max_items: int = None):
    """Update opportunities for a specific source with detailed information."""
    from opportunity_radar.models.opportunity import Opportunity
    from opportunity_radar.scrapers.hackerone_scraper import HackerOneScraper
    from opportunity_radar.scrapers.grants_gov_scraper import GrantsGovScraper
    from opportunity_radar.scrapers.eu_horizon_scraper import EUHorizonScraper

    # Map source to scraper
    scraper_map = {
        "hackerone": HackerOneScraper,
        "grants_gov": GrantsGovScraper,
        "eu_horizon": EUHorizonScraper,
    }

    if source not in scraper_map:
        logger.error(f"Unknown source: {source}. Available: {list(scraper_map.keys())}")
        return

    # Create scraper instance
    scraper_class = scraper_map[source]
    scraper = scraper_class(request_delay=1.5)

    try:
        # Find opportunities for this source
        query = {"$or": [
            {"source_url": {"$regex": source.replace("_", ""), "$options": "i"}},
            {"external_id": {"$regex": source.replace("_", "-"), "$options": "i"}},
        ]}

        # For HackerOne, check for h1- prefix
        if source == "hackerone":
            query = {"external_id": {"$regex": "^h1-", "$options": "i"}}
        elif source == "grants_gov":
            query = {"external_id": {"$regex": "^grants-gov-", "$options": "i"}}
        elif source == "eu_horizon":
            query = {"external_id": {"$regex": "^eu-", "$options": "i"}}

        opportunities = await Opportunity.find(query).to_list()

        if max_items:
            opportunities = opportunities[:max_items]

        logger.info(f"Found {len(opportunities)} {source} opportunities to update")

        updated = 0
        failed = 0
        skipped = 0

        for i, opp in enumerate(opportunities):
            try:
                # Get the URL for scraping
                url = opp.source_url or opp.website_url
                external_id = opp.external_id

                if not url or not external_id:
                    logger.warning(f"Skipping {opp.title}: missing URL or external_id")
                    skipped += 1
                    continue

                logger.info(f"[{i+1}/{len(opportunities)}] Updating: {opp.title[:50]}...")

                # Scrape detailed information
                detailed = await scraper.scrape_detail(external_id, url)

                if detailed:
                    # Update the opportunity with detailed info
                    update_fields = {}

                    if detailed.description and len(detailed.description) > len(opp.description or ""):
                        update_fields["description"] = detailed.description

                    if detailed.themes and len(detailed.themes) > len(opp.themes or []):
                        update_fields["themes"] = detailed.themes

                    if detailed.tags and len(detailed.tags) > len(opp.technologies or []):
                        update_fields["technologies"] = detailed.tags

                    if detailed.total_prize_amount and not opp.total_prize_value:
                        update_fields["total_prize_value"] = detailed.total_prize_amount

                    if detailed.prizes and len(detailed.prizes) > len(opp.prizes or []):
                        update_fields["prizes"] = detailed.prizes

                    if detailed.eligibility_rules and len(detailed.eligibility_rules) > len(opp.requirements or []):
                        update_fields["requirements"] = detailed.eligibility_rules

                    if detailed.raw_data:
                        update_fields["raw_data"] = detailed.raw_data

                    if update_fields:
                        await opp.set(update_fields)
                        updated += 1
                        logger.info(f"  Updated fields: {list(update_fields.keys())}")
                    else:
                        skipped += 1
                        logger.debug(f"  No new data to update")
                else:
                    failed += 1
                    logger.warning(f"  Failed to fetch details")

                # Rate limiting
                await asyncio.sleep(scraper.request_delay)

            except Exception as e:
                failed += 1
                logger.error(f"  Error updating {opp.title}: {e}")

            # Progress log every 10 items
            if (i + 1) % 10 == 0:
                logger.info(f"Progress: {i+1}/{len(opportunities)} - Updated: {updated}, Failed: {failed}, Skipped: {skipped}")

        logger.info(f"\n{'='*50}")
        logger.info(f"Update complete for {source}:")
        logger.info(f"  Total: {len(opportunities)}")
        logger.info(f"  Updated: {updated}")
        logger.info(f"  Failed: {failed}")
        logger.info(f"  Skipped: {skipped}")
        logger.info(f"{'='*50}\n")

    finally:
        await scraper.close()


async def main():
    """Main function to update opportunity details."""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Get MongoDB connection
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DB_NAME", "opportunity_radar")

    logger.info(f"Connecting to MongoDB: {mongo_url}")

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    # Initialize Beanie
    from opportunity_radar.models.opportunity import Opportunity, Host

    await init_beanie(
        database=db,
        document_models=[Opportunity, Host]
    )

    logger.info("Connected to MongoDB")

    # Parse command line arguments
    sources = sys.argv[1:] if len(sys.argv) > 1 else ["hackerone", "grants_gov", "eu_horizon"]

    # Check for max items flag
    max_items = None
    if "--max" in sources:
        idx = sources.index("--max")
        if idx + 1 < len(sources):
            try:
                max_items = int(sources[idx + 1])
                sources = sources[:idx] + sources[idx+2:]
            except ValueError:
                pass

    for source in sources:
        if source.startswith("--"):
            continue
        logger.info(f"\n{'='*50}")
        logger.info(f"Processing source: {source}")
        logger.info(f"{'='*50}")
        await update_opportunities_for_source(source, max_items)

    client.close()
    logger.info("Done!")


if __name__ == "__main__":
    asyncio.run(main())
