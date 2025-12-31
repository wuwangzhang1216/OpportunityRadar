"""Y Combinator and startup accelerator scraper."""

import asyncio
import logging
import re
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from bs4 import BeautifulSoup

from .base import BaseScraper, RawOpportunity, ScraperResult, ScraperStatus, with_retry

if TYPE_CHECKING:
    from playwright.async_api import Page, Browser

logger = logging.getLogger(__name__)


class YCombinatorScraper(BaseScraper):
    """
    Scraper for Y Combinator and major startup accelerators.

    Covers:
    - Y Combinator (YC)
    - Techstars
    - 500 Global (formerly 500 Startups)
    - Other major accelerators
    """

    # Accelerator URLs to scrape
    ACCELERATORS = {
        "yc": {
            "name": "Y Combinator",
            "url": "https://www.ycombinator.com/apply",
            "funding": 500000,
            "equity": "7%",
        },
        "techstars": {
            "name": "Techstars",
            "url": "https://www.techstars.com/accelerators",
            "funding": 120000,
            "equity": "6%",
        },
        "500global": {
            "name": "500 Global",
            "url": "https://500.co/accelerators",
            "funding": 150000,
            "equity": "6%",
        },
    }

    def __init__(self, headless: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.headless = headless
        self._browser: Optional["Browser"] = None
        self._playwright = None

    @property
    def source_name(self) -> str:
        return "accelerators"

    @property
    def base_url(self) -> str:
        return "https://www.ycombinator.com"

    async def _get_browser(self) -> "Browser":
        """Get or create Playwright browser instance."""
        if self._browser is None or not self._browser.is_connected():
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
            )
            logger.info("Accelerators: Playwright browser launched")

        return self._browser

    async def _create_page(self) -> "Page":
        """Create a new browser page."""
        browser = await self._get_browser()
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        return await context.new_page()

    async def close(self):
        """Close browser and HTTP client."""
        if self._browser and self._browser.is_connected():
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        await super().close()

    @with_retry(max_attempts=3)
    async def scrape_list(self, page: int = 1) -> ScraperResult:
        """Scrape accelerator programs."""
        opportunities: List[RawOpportunity] = []
        errors: List[str] = []

        # Only run on first page since accelerators are limited
        if page > 1:
            return ScraperResult(
                opportunities=[],
                status=ScraperStatus.SUCCESS,
                source=self.source_name,
                total_found=0,
            )

        # Add Y Combinator
        yc_opp = await self._scrape_yc()
        if yc_opp:
            opportunities.append(yc_opp)

        # Add Techstars programs
        techstars_opps = await self._scrape_techstars()
        opportunities.extend(techstars_opps)

        # Add other known accelerators
        known_opps = self._get_known_accelerators()
        opportunities.extend(known_opps)

        # Deduplicate by external_id
        seen_ids = set()
        unique_opps = []
        for opp in opportunities:
            if opp.external_id not in seen_ids:
                seen_ids.add(opp.external_id)
                unique_opps.append(opp)

        return ScraperResult(
            opportunities=unique_opps,
            status=ScraperStatus.SUCCESS if unique_opps else ScraperStatus.PARTIAL,
            source=self.source_name,
            total_found=len(unique_opps),
            errors=errors,
            metadata={"page": page},
        )

    async def _scrape_yc(self) -> Optional[RawOpportunity]:
        """Scrape Y Combinator application info."""
        try:
            client = await self.get_client()
            response = await client.get("https://www.ycombinator.com/apply")

            if response.status_code != 200:
                return self._create_yc_fallback()

            soup = BeautifulSoup(response.text, "lxml")

            # Try to find deadline
            deadline = None
            deadline_elem = soup.select_one("[class*='deadline'], [class*='date'], time")
            if deadline_elem:
                deadline = deadline_elem.get_text(strip=True)

            # Description
            desc_elem = soup.select_one("main p, .hero p, article p")
            description = desc_elem.get_text(strip=True)[:1000] if desc_elem else ""

            if not description:
                description = (
                    "Y Combinator is the world's most successful startup accelerator. "
                    "YC has funded over 4,000 companies including Airbnb, Dropbox, Stripe, "
                    "Reddit, DoorDash, Coinbase, and Instacart. YC provides $500,000 in "
                    "funding for 7% equity, plus extensive mentorship and network access."
                )

            return RawOpportunity(
                source=self.source_name,
                external_id="acc-ycombinator",
                title="Y Combinator Startup Accelerator",
                url="https://www.ycombinator.com/apply",
                description=description,
                image_url="https://www.ycombinator.com/assets/ycdc/yc-og-image.png",
                submission_deadline=deadline,
                location="San Francisco, CA / Remote",
                is_online=False,
                regions=["US", "Global"],
                total_prize_amount=500000,
                prize_currency="USD",
                tags=["accelerator", "yc", "y-combinator", "startup", "funding", "equity"],
                themes=["startup", "entrepreneurship", "funding", "mentorship"],
                tech_stack=[],
                host_name="Y Combinator",
                host_url="https://www.ycombinator.com",
                raw_data={"equity": "7%", "batch_size": "~200 companies"},
            )

        except Exception as e:
            logger.warning(f"Failed to scrape YC: {e}")
            return self._create_yc_fallback()

    def _create_yc_fallback(self) -> RawOpportunity:
        """Create YC opportunity with known data."""
        return RawOpportunity(
            source=self.source_name,
            external_id="acc-ycombinator",
            title="Y Combinator Startup Accelerator",
            url="https://www.ycombinator.com/apply",
            description=(
                "Y Combinator is the world's most successful startup accelerator, "
                "having funded over 4,000 companies including Airbnb, Dropbox, Stripe, "
                "and Coinbase. YC provides $500,000 in funding for 7% equity."
            ),
            location="San Francisco, CA / Remote",
            is_online=False,
            regions=["US", "Global"],
            total_prize_amount=500000,
            prize_currency="USD",
            tags=["accelerator", "yc", "startup", "funding"],
            themes=["startup", "entrepreneurship", "funding"],
            host_name="Y Combinator",
            host_url="https://www.ycombinator.com",
        )

    async def _scrape_techstars(self) -> List[RawOpportunity]:
        """Scrape Techstars accelerator programs."""
        opportunities = []

        try:
            client = await self.get_client()
            response = await client.get("https://www.techstars.com/accelerators")

            if response.status_code != 200:
                return self._get_techstars_fallback()

            soup = BeautifulSoup(response.text, "lxml")

            # Find program cards
            cards = soup.select("[class*='program'], [class*='accelerator'], .card")

            for card in cards[:20]:  # Limit to 20
                try:
                    title_elem = card.select_one("h2, h3, h4, .title")
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    if not title or "techstars" not in title.lower():
                        continue

                    link = card.select_one("a")
                    href = link.get("href", "") if link else ""
                    url = href if href.startswith("http") else f"https://www.techstars.com{href}"

                    # Extract location
                    loc_elem = card.select_one("[class*='location'], .city")
                    location = loc_elem.get_text(strip=True) if loc_elem else "Various Locations"

                    # Description
                    desc_elem = card.select_one("p, .description")
                    description = desc_elem.get_text(strip=True)[:500] if desc_elem else ""

                    external_id = f"acc-techstars-{title.lower().replace(' ', '-')[:30]}"

                    opportunities.append(RawOpportunity(
                        source=self.source_name,
                        external_id=external_id,
                        title=title,
                        url=url,
                        description=description or f"Techstars accelerator program: {title}",
                        location=location,
                        is_online=False,
                        regions=["Global"],
                        total_prize_amount=120000,
                        prize_currency="USD",
                        tags=["accelerator", "techstars", "startup", "funding"],
                        themes=["startup", "entrepreneurship", "mentorship"],
                        host_name="Techstars",
                        host_url="https://www.techstars.com",
                    ))

                except Exception as e:
                    logger.debug(f"Failed to parse Techstars card: {e}")

            if not opportunities:
                opportunities = self._get_techstars_fallback()

        except Exception as e:
            logger.warning(f"Failed to scrape Techstars: {e}")
            opportunities = self._get_techstars_fallback()

        return opportunities

    def _get_techstars_fallback(self) -> List[RawOpportunity]:
        """Return known Techstars programs."""
        programs = [
            ("Techstars NYC", "New York, NY", "Leading accelerator in the NYC startup ecosystem"),
            ("Techstars LA", "Los Angeles, CA", "Entertainment and tech accelerator"),
            ("Techstars Boulder", "Boulder, CO", "Original Techstars program"),
            ("Techstars Seattle", "Seattle, WA", "Pacific Northwest startup accelerator"),
            ("Techstars Austin", "Austin, TX", "Texas startup ecosystem accelerator"),
        ]

        return [
            RawOpportunity(
                source=self.source_name,
                external_id=f"acc-{name.lower().replace(' ', '-')}",
                title=name,
                url="https://www.techstars.com/accelerators",
                description=desc,
                location=loc,
                is_online=False,
                regions=["US"],
                total_prize_amount=120000,
                prize_currency="USD",
                tags=["accelerator", "techstars", "startup"],
                themes=["startup", "entrepreneurship"],
                host_name="Techstars",
                host_url="https://www.techstars.com",
            )
            for name, loc, desc in programs
        ]

    def _get_known_accelerators(self) -> List[RawOpportunity]:
        """Return list of well-known accelerators."""
        accelerators = [
            {
                "id": "500global",
                "name": "500 Global Accelerator",
                "url": "https://500.co/accelerators",
                "description": "Global venture capital firm and startup accelerator. 500 Global has invested in over 2,800 companies across 80+ countries.",
                "funding": 150000,
                "location": "San Francisco / Global",
                "equity": "6%",
            },
            {
                "id": "plug-and-play",
                "name": "Plug and Play Tech Center",
                "url": "https://www.plugandplaytechcenter.com",
                "description": "Silicon Valley's largest accelerator. Industry-specific programs in fintech, health, supply chain, and more.",
                "funding": 50000,
                "location": "Sunnyvale, CA",
                "equity": "0-3%",
            },
            {
                "id": "alchemist",
                "name": "Alchemist Accelerator",
                "url": "https://alchemistaccelerator.com",
                "description": "Enterprise startup accelerator focused on B2B companies with seed funding and corporate partnerships.",
                "funding": 36000,
                "location": "San Francisco, CA",
                "equity": "5%",
            },
            {
                "id": "antler",
                "name": "Antler",
                "url": "https://www.antler.co",
                "description": "Global early-stage VC and accelerator. Helps founders build companies from day one across 25+ locations.",
                "funding": 150000,
                "location": "Global (25+ locations)",
                "equity": "10%",
            },
            {
                "id": "seedcamp",
                "name": "Seedcamp",
                "url": "https://seedcamp.com",
                "description": "Europe's leading seed fund and accelerator. Backed Revolut, Wise, UiPath, and 400+ companies.",
                "funding": 200000,
                "location": "London, UK / Europe",
                "equity": "7%",
            },
            {
                "id": "entrepreneur-first",
                "name": "Entrepreneur First",
                "url": "https://www.joinef.com",
                "description": "Talent investor that helps individuals build startups. Programs in London, Paris, Berlin, Singapore, Bangalore.",
                "funding": 125000,
                "location": "Global",
                "equity": "10%",
            },
            {
                "id": "gener8tor",
                "name": "gener8tor",
                "url": "https://www.gener8tor.com",
                "description": "Top-ranked US accelerator with programs across the Midwest and beyond.",
                "funding": 100000,
                "location": "Various US locations",
                "equity": "6%",
            },
            {
                "id": "startx",
                "name": "StartX",
                "url": "https://startx.com",
                "description": "Stanford-affiliated accelerator. No equity taken. Strong alumni network.",
                "funding": 0,
                "location": "Palo Alto, CA",
                "equity": "0%",
            },
        ]

        return [
            RawOpportunity(
                source=self.source_name,
                external_id=f"acc-{acc['id']}",
                title=acc["name"],
                url=acc["url"],
                description=acc["description"],
                location=acc["location"],
                is_online=False,
                regions=["Global"],
                total_prize_amount=acc["funding"],
                prize_currency="USD",
                tags=["accelerator", "startup", "funding", "equity", "mentorship"],
                themes=["startup", "entrepreneurship", "venture-capital"],
                host_name=acc["name"].split()[0],
                host_url=acc["url"],
                raw_data={"equity": acc["equity"]},
            )
            for acc in accelerators
        ]

    async def scrape_detail(self, external_id: str, url: str) -> Optional[RawOpportunity]:
        """Scrape detailed accelerator information."""
        # Most details already captured in list
        return None


def create_ycombinator_scraper(**kwargs) -> YCombinatorScraper:
    """Create a YCombinator/Accelerator scraper instance."""
    return YCombinatorScraper(**kwargs)
