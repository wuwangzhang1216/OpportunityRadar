"""Scraper scheduler for periodic data collection."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Type

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .base import BaseScraper, ScraperResult, ScraperStatus
from .devpost_scraper import DevpostScraper
from .mlh_scraper import MLHScraper
from .ethglobal_scraper import ETHGlobalScraper
from .kaggle_scraper import KaggleScraper
from .hackerearth_scraper import HackerEarthScraper
# Government funding scrapers
from .grants_gov_scraper import GrantsGovScraper
from .sbir_scraper import SBIRScraper
from .eu_horizon_scraper import EUHorizonScraper
from .innovate_uk_scraper import InnovateUKScraper
# Other opportunity scrapers
from .hackerone_scraper import HackerOneScraper
from .ycombinator_scraper import YCombinatorScraper
from .opensource_grants_scraper import OpenSourceGrantsScraper
from .normalizer import DataNormalizer
from ..config import settings

logger = logging.getLogger(__name__)


class ScraperRegistry:
    """Registry of available scrapers."""

    _scrapers: Dict[str, Type[BaseScraper]] = {
        # Hackathons
        "devpost": DevpostScraper,
        "mlh": MLHScraper,
        "ethglobal": ETHGlobalScraper,
        "kaggle": KaggleScraper,
        "hackerearth": HackerEarthScraper,
        # Government funding
        "grants_gov": GrantsGovScraper,
        "sbir": SBIRScraper,
        "eu_horizon": EUHorizonScraper,
        "innovate_uk": InnovateUKScraper,
        # Bug bounties
        "hackerone": HackerOneScraper,
        # Accelerators
        "accelerators": YCombinatorScraper,
        # Open source
        "opensource_grants": OpenSourceGrantsScraper,
    }

    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseScraper]]:
        """Get scraper class by name."""
        return cls._scrapers.get(name)

    @classmethod
    def list_all(cls) -> List[str]:
        """List all registered scrapers."""
        return list(cls._scrapers.keys())

    @classmethod
    def register(cls, name: str, scraper_class: Type[BaseScraper]):
        """Register a new scraper."""
        cls._scrapers[name] = scraper_class


class ScraperManager:
    """Manager for running and coordinating scrapers."""

    def __init__(
        self,
        request_delay: float = 2.0,
        max_pages: int = 20,
    ):
        self.request_delay = request_delay
        self.max_pages = max_pages
        self.normalizer = DataNormalizer()
        self._results: Dict[str, ScraperResult] = {}
        self._last_run: Dict[str, datetime] = {}

    async def run_scraper(
        self,
        scraper_name: str,
        max_pages: Optional[int] = None,
        **kwargs,
    ) -> ScraperResult:
        """Run a single scraper."""
        scraper_class = ScraperRegistry.get(scraper_name)
        if not scraper_class:
            logger.error(f"Unknown scraper: {scraper_name}")
            return ScraperResult(
                opportunities=[],
                status=ScraperStatus.FAILED,
                source=scraper_name,
                error_message=f"Unknown scraper: {scraper_name}",
            )

        logger.info(f"Starting scraper: {scraper_name}")

        try:
            scraper = scraper_class(
                request_delay=self.request_delay,
                max_pages=max_pages or self.max_pages,
                **kwargs,
            )

            # Run the scraper
            result = await scraper.scrape_all(max_pages=max_pages)

            # Store results
            self._results[scraper_name] = result
            self._last_run[scraper_name] = datetime.utcnow()

            logger.info(
                f"Scraper {scraper_name} completed: "
                f"{result.total_found} opportunities, status={result.status.value}"
            )

            # Cleanup
            await scraper.close()

            return result

        except Exception as e:
            logger.error(f"Scraper {scraper_name} failed: {e}")
            return ScraperResult(
                opportunities=[],
                status=ScraperStatus.FAILED,
                source=scraper_name,
                error_message=str(e),
            )

    async def run_all_scrapers(self, scraper_names: Optional[List[str]] = None) -> Dict[str, ScraperResult]:
        """Run multiple scrapers sequentially."""
        scrapers_to_run = scraper_names or ScraperRegistry.list_all()
        results = {}

        for scraper_name in scrapers_to_run:
            # Check if enabled in settings
            if scraper_name == "devpost" and not settings.scraper_devpost_enabled:
                logger.info(f"Skipping disabled scraper: {scraper_name}")
                continue
            if scraper_name == "mlh" and not settings.scraper_mlh_enabled:
                logger.info(f"Skipping disabled scraper: {scraper_name}")
                continue

            result = await self.run_scraper(scraper_name)
            results[scraper_name] = result

            # Delay between scrapers
            await asyncio.sleep(self.request_delay)

        return results

    def get_last_result(self, scraper_name: str) -> Optional[ScraperResult]:
        """Get the last result for a scraper."""
        return self._results.get(scraper_name)

    def get_last_run_time(self, scraper_name: str) -> Optional[datetime]:
        """Get the last run time for a scraper."""
        return self._last_run.get(scraper_name)

    def get_stats(self) -> Dict:
        """Get statistics for all scrapers."""
        stats = {}
        for name in ScraperRegistry.list_all():
            result = self._results.get(name)
            stats[name] = {
                "last_run": self._last_run.get(name),
                "status": result.status.value if result else None,
                "total_found": result.total_found if result else 0,
                "errors": len(result.errors) if result else 0,
            }
        return stats


class ScraperScheduler:
    """Scheduler for periodic scraper execution."""

    def __init__(self, manager: Optional[ScraperManager] = None):
        self.manager = manager or ScraperManager()
        self.scheduler = AsyncIOScheduler()
        self._is_running = False

    def setup_jobs(self):
        """Configure scheduled scraping jobs."""
        interval_hours = settings.scraper_interval_hours

        # Devpost scraper - runs every N hours
        if settings.scraper_devpost_enabled:
            self.scheduler.add_job(
                self._run_devpost_scrape,
                IntervalTrigger(hours=interval_hours),
                id="devpost_scrape",
                name="Devpost Hackathon Scraper",
                replace_existing=True,
            )
            logger.info(f"Scheduled Devpost scraper every {interval_hours} hours")

        # MLH scraper - runs every N hours
        if settings.scraper_mlh_enabled:
            self.scheduler.add_job(
                self._run_mlh_scrape,
                IntervalTrigger(hours=interval_hours),
                id="mlh_scrape",
                name="MLH Hackathon Scraper",
                replace_existing=True,
            )
            logger.info(f"Scheduled MLH scraper every {interval_hours} hours")

        # Daily health check at 3 AM UTC
        self.scheduler.add_job(
            self._run_health_check,
            CronTrigger(hour=3, minute=0),
            id="health_check",
            name="Scraper Health Check",
            replace_existing=True,
        )

        # Deadline reminder check - runs every 6 hours
        self.scheduler.add_job(
            self._run_deadline_check,
            IntervalTrigger(hours=6),
            id="deadline_check",
            name="Deadline Reminder Check",
            replace_existing=True,
        )
        logger.info("Scheduled deadline reminder check every 6 hours")

    async def _run_devpost_scrape(self):
        """Execute Devpost scraping job."""
        logger.info("Starting scheduled Devpost scrape...")
        try:
            result = await self.manager.run_scraper("devpost")
            if result.success:
                logger.info(f"Devpost scrape completed: {result.total_found} opportunities")
                # Persist to database
                from ..services.scraper_persistence_service import get_scraper_persistence_service
                service = get_scraper_persistence_service()
                stats = await service.persist_scraper_result(result)
                logger.info(f"Devpost persistence: {stats['inserted']} inserted, {stats['updated']} updated")
            else:
                logger.error(f"Devpost scrape failed: {result.error_message}")
        except Exception as e:
            logger.error(f"Devpost scrape job failed: {e}")

    async def _run_mlh_scrape(self):
        """Execute MLH scraping job."""
        logger.info("Starting scheduled MLH scrape...")
        try:
            result = await self.manager.run_scraper("mlh")
            if result.success:
                logger.info(f"MLH scrape completed: {result.total_found} opportunities")
                # Persist to database
                from ..services.scraper_persistence_service import get_scraper_persistence_service
                service = get_scraper_persistence_service()
                stats = await service.persist_scraper_result(result)
                logger.info(f"MLH persistence: {stats['inserted']} inserted, {stats['updated']} updated")
            else:
                logger.error(f"MLH scrape failed: {result.error_message}")
        except Exception as e:
            logger.error(f"MLH scrape job failed: {e}")

    async def _run_health_check(self):
        """Run health check for all scrapers."""
        logger.info("Running scraper health check...")
        for name in ScraperRegistry.list_all():
            scraper_class = ScraperRegistry.get(name)
            if scraper_class:
                scraper = scraper_class()
                try:
                    is_healthy = await scraper.health_check()
                    logger.info(f"Scraper {name} health: {'OK' if is_healthy else 'FAILED'}")
                finally:
                    await scraper.close()

    async def _run_deadline_check(self):
        """Check for upcoming deadlines and send reminders."""
        logger.info("Running deadline reminder check...")
        try:
            from ..services.notification_service import get_notification_service
            service = get_notification_service()
            stats = await service.check_deadline_reminders()
            logger.info(
                f"Deadline check complete: {stats['reminders_sent']} reminders sent, "
                f"{stats['users_checked']} users checked"
            )
        except Exception as e:
            logger.error(f"Deadline check failed: {e}")

    def start(self):
        """Start the scheduler."""
        if not self._is_running:
            self.setup_jobs()
            self.scheduler.start()
            self._is_running = True
            logger.info("Scraper scheduler started")

    def stop(self):
        """Stop the scheduler."""
        if self._is_running:
            self.scheduler.shutdown(wait=False)
            self._is_running = False
            logger.info("Scraper scheduler stopped")

    def get_jobs(self) -> List[Dict]:
        """Get list of scheduled jobs."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time,
                "trigger": str(job.trigger),
            })
        return jobs

    @property
    def is_running(self) -> bool:
        return self._is_running


# Global instances
scraper_manager = ScraperManager(
    request_delay=settings.scraper_request_delay_seconds,
)
scraper_scheduler = ScraperScheduler(manager=scraper_manager)
