#!/usr/bin/env python3
"""Populate database with opportunities from all scrapers."""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class OpportunityPopulator:
    """Populate database with scraped opportunities."""

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

    # Scrapers that need headless browser
    PLAYWRIGHT_SCRAPERS = {
        "mlh",
        "ethglobal",
        "kaggle",
        "hackerearth",
        "sbir",
        "accelerators",
        "opensource_grants",
    }

    def __init__(self):
        self.stats: Dict[str, dict] = {}

    async def connect(self):
        """Initialize database connection."""
        from src.opportunity_radar.db.mongodb import init_db

        await init_db()
        logger.info("Connected to MongoDB")

    async def close(self):
        """Close database connection."""
        from src.opportunity_radar.db.mongodb import close_db

        await close_db()

    async def populate_from_scraper(
        self,
        scraper_name: str,
        max_pages: int = 2,
        fetch_details: bool = False,
    ) -> dict:
        """Populate opportunities from a single scraper."""
        from src.opportunity_radar.scrapers import ScraperRegistry
        from src.opportunity_radar.models.opportunity import Opportunity

        logger.info(f"Starting: {scraper_name}")

        scraper_class = ScraperRegistry.get(scraper_name)
        if not scraper_class:
            logger.error(f"Unknown scraper: {scraper_name}")
            return {"status": "error", "error": "Unknown scraper"}

        # Create scraper instance with appropriate options
        kwargs = {}
        if scraper_name in self.PLAYWRIGHT_SCRAPERS:
            kwargs["headless"] = True

        scraper = scraper_class(**kwargs)

        stats = {
            "scraper": scraper_name,
            "status": "success",
            "scraped": 0,
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "errors": [],
        }

        try:
            # Scrape data
            if fetch_details:
                result = await scraper.scrape_all(
                    max_pages=max_pages,
                    fetch_details=True,
                    max_details=10,
                )
            else:
                result = await scraper.scrape_list(page=1)

            stats["scraped"] = len(result.opportunities)
            stats["scraper_status"] = result.status.value

            if result.errors:
                stats["errors"].extend(result.errors[:5])

            logger.info(f"  Scraped {stats['scraped']} opportunities")

            # Save to database
            for raw_opp in result.opportunities:
                try:
                    # Check if already exists
                    existing = await Opportunity.find_one(
                        Opportunity.external_id == raw_opp.external_id
                    )

                    if existing:
                        # Update existing record
                        existing.title = raw_opp.title
                        existing.description = raw_opp.description
                        existing.total_prize_value = raw_opp.total_prize_amount
                        existing.themes = raw_opp.themes or []
                        existing.technologies = raw_opp.tech_stack or []
                        existing.updated_at = datetime.utcnow()
                        await existing.save()
                        stats["updated"] += 1
                    else:
                        # Create new record
                        opp = Opportunity(
                            external_id=raw_opp.external_id,
                            title=raw_opp.title,
                            description=raw_opp.description,
                            short_description=(
                                raw_opp.description[:200] if raw_opp.description else None
                            ),
                            opportunity_type=self.TYPE_MAPPING.get(scraper_name, "other"),
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

                except Exception as e:
                    stats["skipped"] += 1
                    if len(stats["errors"]) < 10:
                        stats["errors"].append(
                            f"{raw_opp.external_id}: {str(e)[:80]}"
                        )

            logger.info(
                f"  Inserted: {stats['inserted']}, Updated: {stats['updated']}, Skipped: {stats['skipped']}"
            )

        except Exception as e:
            stats["status"] = "error"
            stats["errors"].append(str(e))
            logger.error(f"  Error: {e}")

        finally:
            await scraper.close()

        return stats

    async def populate_all(
        self,
        scrapers: Optional[List[str]] = None,
        max_pages: int = 2,
        fetch_details: bool = False,
    ):
        """Populate from all scrapers."""
        from src.opportunity_radar.scrapers import ScraperRegistry

        if scrapers is None:
            scrapers = ScraperRegistry.list_all()

        logger.info(f"Populating from {len(scrapers)} scrapers: {scrapers}")

        for scraper_name in scrapers:
            stats = await self.populate_from_scraper(
                scraper_name,
                max_pages=max_pages,
                fetch_details=fetch_details,
            )
            self.stats[scraper_name] = stats

            # Delay between scrapers to avoid rate limiting
            await asyncio.sleep(3)

        self.print_summary()

    def print_summary(self):
        """Print population summary."""
        print("\n" + "=" * 70)
        print("POPULATION SUMMARY")
        print("=" * 70)

        total_inserted = 0
        total_updated = 0
        total_scraped = 0

        for name, stats in self.stats.items():
            status = "[OK]" if stats["status"] == "success" else "[ERR]"
            print(f"\n{status} {name}:")
            print(f"    Scraped:  {stats.get('scraped', 0)}")
            print(f"    Inserted: {stats.get('inserted', 0)}")
            print(f"    Updated:  {stats.get('updated', 0)}")
            print(f"    Skipped:  {stats.get('skipped', 0)}")

            if stats.get("errors"):
                print(f"    Errors ({len(stats['errors'])}):")
                for err in stats["errors"][:3]:
                    print(f"      - {err[:70]}")

            total_inserted += stats.get("inserted", 0)
            total_updated += stats.get("updated", 0)
            total_scraped += stats.get("scraped", 0)

        print("\n" + "-" * 70)
        print(f"TOTAL: {total_scraped} scraped, {total_inserted} inserted, {total_updated} updated")


async def main():
    parser = argparse.ArgumentParser(description="Populate opportunities database")
    parser.add_argument(
        "--scrapers", "-s", nargs="+", help="Specific scrapers to run (space-separated)"
    )
    parser.add_argument(
        "--pages", "-p", type=int, default=2, help="Max pages per scraper (default: 2)"
    )
    parser.add_argument(
        "--details", "-d", action="store_true", help="Fetch detailed info for each opportunity"
    )
    parser.add_argument(
        "--quick",
        "-q",
        action="store_true",
        help="Quick mode: only run API-based scrapers (devpost, hackerone, grants_gov)",
    )
    parser.add_argument(
        "--list", "-l", action="store_true", help="List available scrapers and exit"
    )

    args = parser.parse_args()

    # List scrapers and exit
    if args.list:
        from src.opportunity_radar.scrapers import ScraperRegistry

        print("Available scrapers:")
        for name in ScraperRegistry.list_all():
            scraper_type = OpportunityPopulator.TYPE_MAPPING.get(name, "other")
            is_playwright = "Playwright" if name in OpportunityPopulator.PLAYWRIGHT_SCRAPERS else "HTTP"
            print(f"  - {name:20} ({scraper_type:12}, {is_playwright})")
        return

    populator = OpportunityPopulator()

    try:
        await populator.connect()

        scrapers = args.scrapers
        if args.quick:
            scrapers = ["devpost", "hackerone", "grants_gov"]
            logger.info("Quick mode: using API-based scrapers only")

        await populator.populate_all(
            scrapers=scrapers,
            max_pages=args.pages,
            fetch_details=args.details,
        )

    finally:
        await populator.close()


if __name__ == "__main__":
    asyncio.run(main())
