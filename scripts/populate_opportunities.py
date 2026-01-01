"""Populate MongoDB with opportunities from scrapers."""

import asyncio
import logging
import sys
from datetime import datetime

sys.path.insert(0, "e:\\OpportunityRadar")

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


async def populate():
    """Run scrapers and save opportunities to MongoDB."""
    from src.opportunity_radar.models.opportunity import Opportunity, Host
    from src.opportunity_radar.scrapers import (
        DevpostScraper, MLHScraper, ETHGlobalScraper,
        KaggleScraper, HackerEarthScraper
    )

    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(
        database=client["opportunity_radar"],
        document_models=[Opportunity, Host]
    )

    scrapers = [
        ('Devpost', DevpostScraper(), 'hackathon'),
        ('MLH', MLHScraper(headless=True), 'hackathon'),
        ('ETHGlobal', ETHGlobalScraper(headless=True), 'hackathon'),
        ('Kaggle', KaggleScraper(headless=True), 'competition'),
        ('HackerEarth', HackerEarthScraper(headless=True), 'hackathon'),
    ]

    total_saved = 0

    for name, scraper, category in scrapers:
        logger.info(f"Scraping {name}...")

        try:
            result = await scraper.scrape_list(page=1)
            logger.info(f"  Found {result.total_found} opportunities")

            for raw_opp in result.opportunities:
                try:
                    # Check if already exists
                    existing = await Opportunity.find_one(
                        Opportunity.external_id == raw_opp.external_id
                    )

                    if existing:
                        logger.debug(f"  Skipping existing: {raw_opp.title[:40]}")
                        continue

                    # Create new opportunity
                    opp = Opportunity(
                        external_id=raw_opp.external_id,
                        title=raw_opp.title,
                        description=raw_opp.description,
                        short_description=raw_opp.description[:200] if raw_opp.description else None,
                        opportunity_type=category,
                        format=raw_opp.format if hasattr(raw_opp, 'format') else None,
                        location_city=raw_opp.location if hasattr(raw_opp, 'location') else None,
                        website_url=raw_opp.url,
                        source_url=raw_opp.url,
                        logo_url=raw_opp.image_url if hasattr(raw_opp, 'image_url') else None,
                        banner_url=raw_opp.image_url if hasattr(raw_opp, 'image_url') else None,
                        themes=raw_opp.themes if hasattr(raw_opp, 'themes') else [],
                        technologies=raw_opp.tech_stack if hasattr(raw_opp, 'tech_stack') else [],
                        total_prize_value=raw_opp.total_prize_amount if hasattr(raw_opp, 'total_prize_amount') else None,
                        participant_count=raw_opp.participant_count if hasattr(raw_opp, 'participant_count') else None,
                        is_active=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )

                    await opp.insert()
                    total_saved += 1
                    logger.info(f"  Saved: {raw_opp.title[:50]}")

                except Exception as e:
                    logger.error(f"  Error saving {raw_opp.title[:30]}: {e}")

        except Exception as e:
            logger.error(f"Error scraping {name}: {e}")
        finally:
            await scraper.close()

    logger.info(f"\nTotal opportunities saved: {total_saved}")

    # Show count
    count = await Opportunity.find().count()
    logger.info(f"Total in database: {count}")

    client.close()


if __name__ == "__main__":
    asyncio.run(populate())
