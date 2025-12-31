"""Scrapers package for data ingestion."""

from .base import BaseScraper, RawOpportunity, ScraperResult, ScraperStatus
from .normalizer import DataNormalizer

# Hackathon scrapers
from .devpost_scraper import DevpostScraper, create_devpost_scraper
from .mlh_scraper import MLHScraper, create_mlh_scraper
from .ethglobal_scraper import ETHGlobalScraper, create_ethglobal_scraper
from .kaggle_scraper import KaggleScraper, create_kaggle_scraper
from .hackerearth_scraper import HackerEarthScraper, create_hackerearth_scraper

# Government funding scrapers
from .grants_gov_scraper import GrantsGovScraper, create_grants_gov_scraper
from .sbir_scraper import SBIRScraper, create_sbir_scraper
from .eu_horizon_scraper import EUHorizonScraper, create_eu_horizon_scraper
from .innovate_uk_scraper import InnovateUKScraper, create_innovate_uk_scraper

# Other opportunity scrapers
from .hackerone_scraper import HackerOneScraper, create_hackerone_scraper
from .ycombinator_scraper import YCombinatorScraper, create_ycombinator_scraper
from .opensource_grants_scraper import OpenSourceGrantsScraper, create_opensource_grants_scraper

from .scheduler import ScraperManager, ScraperScheduler, ScraperRegistry, scraper_manager, scraper_scheduler

__all__ = [
    # Base classes
    "BaseScraper",
    "RawOpportunity",
    "ScraperResult",
    "ScraperStatus",
    "DataNormalizer",
    # Hackathon Scrapers
    "DevpostScraper",
    "create_devpost_scraper",
    "MLHScraper",
    "create_mlh_scraper",
    "ETHGlobalScraper",
    "create_ethglobal_scraper",
    "KaggleScraper",
    "create_kaggle_scraper",
    "HackerEarthScraper",
    "create_hackerearth_scraper",
    # Government Funding Scrapers
    "GrantsGovScraper",
    "create_grants_gov_scraper",
    "SBIRScraper",
    "create_sbir_scraper",
    "EUHorizonScraper",
    "create_eu_horizon_scraper",
    "InnovateUKScraper",
    "create_innovate_uk_scraper",
    # Other Opportunity Scrapers
    "HackerOneScraper",
    "create_hackerone_scraper",
    "YCombinatorScraper",
    "create_ycombinator_scraper",
    "OpenSourceGrantsScraper",
    "create_opensource_grants_scraper",
    # Scheduler
    "ScraperManager",
    "ScraperScheduler",
    "ScraperRegistry",
    "scraper_manager",
    "scraper_scheduler",
]
