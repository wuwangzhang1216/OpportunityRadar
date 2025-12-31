"""Open source grants and funding scraper."""

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


class OpenSourceGrantsScraper(BaseScraper):
    """
    Scraper for open source funding and grants.

    Covers:
    - GitHub Sponsors
    - Open Collective foundations
    - Foundation grants (Mozilla, Linux, Apache, etc.)
    - Google Summer of Code
    - Outreachy
    """

    def __init__(self, headless: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.headless = headless
        self._browser: Optional["Browser"] = None
        self._playwright = None

    @property
    def source_name(self) -> str:
        return "opensource_grants"

    @property
    def base_url(self) -> str:
        return "https://github.com/sponsors"

    async def _get_browser(self) -> "Browser":
        """Get or create Playwright browser instance."""
        if self._browser is None or not self._browser.is_connected():
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
            )
            logger.info("OpenSource Grants: Playwright browser launched")

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
        """Scrape open source funding opportunities."""
        opportunities: List[RawOpportunity] = []
        errors: List[str] = []

        # Only run on first page since grants are curated
        if page > 1:
            return ScraperResult(
                opportunities=[],
                status=ScraperStatus.SUCCESS,
                source=self.source_name,
                total_found=0,
            )

        # Collect from various sources
        try:
            # Google Summer of Code
            gsoc = await self._scrape_gsoc()
            if gsoc:
                opportunities.append(gsoc)

            # Outreachy
            outreachy = await self._scrape_outreachy()
            if outreachy:
                opportunities.append(outreachy)

            # Foundation grants
            foundation_grants = self._get_foundation_grants()
            opportunities.extend(foundation_grants)

            # GitHub Sponsors Fund
            gh_sponsors = self._get_github_sponsors_info()
            if gh_sponsors:
                opportunities.append(gh_sponsors)

            # Open Collective grants
            oc_grants = await self._scrape_open_collective()
            opportunities.extend(oc_grants)

            logger.info(f"Found {len(opportunities)} open source funding opportunities")

            return ScraperResult(
                opportunities=opportunities,
                status=ScraperStatus.SUCCESS if opportunities else ScraperStatus.PARTIAL,
                source=self.source_name,
                total_found=len(opportunities),
                errors=errors,
                metadata={"page": page},
            )

        except Exception as e:
            logger.error(f"Open source grants scraping failed: {e}")
            # Return fallback data
            return ScraperResult(
                opportunities=self._get_foundation_grants(),
                status=ScraperStatus.PARTIAL,
                source=self.source_name,
                error_message=str(e),
            )

    async def _scrape_gsoc(self) -> Optional[RawOpportunity]:
        """Scrape Google Summer of Code info."""
        try:
            client = await self.get_client()
            response = await client.get("https://summerofcode.withgoogle.com")

            if response.status_code != 200:
                return self._create_gsoc_fallback()

            soup = BeautifulSoup(response.text, "lxml")

            # Try to find deadline/timeline info
            timeline_elem = soup.select_one("[class*='timeline'], [class*='date']")
            deadline = timeline_elem.get_text(strip=True) if timeline_elem else None

            desc_elem = soup.select_one("main p, .hero p, [class*='description']")
            description = desc_elem.get_text(strip=True)[:1000] if desc_elem else ""

            if not description:
                description = (
                    "Google Summer of Code is a global program that matches students and beginners "
                    "with open source organizations. Contributors work on a 12+ week programming "
                    "project under the guidance of mentors."
                )

            return RawOpportunity(
                source=self.source_name,
                external_id="oss-gsoc",
                title="Google Summer of Code (GSoC)",
                url="https://summerofcode.withgoogle.com",
                description=description,
                image_url="https://summerofcode.withgoogle.com/assets/media/gsoc-2024-badge.svg",
                submission_deadline=deadline,
                location="Online",
                is_online=True,
                regions=["Global"],
                total_prize_amount=3000,  # Standard stipend
                prize_currency="USD",
                tags=["gsoc", "google", "open-source", "mentorship", "students", "programming"],
                themes=["open-source", "mentorship", "education", "programming"],
                tech_stack=["various"],
                host_name="Google",
                host_url="https://summerofcode.withgoogle.com",
                student_only=True,
                raw_data={"stipend": "$1500-$3000 depending on location", "duration": "12+ weeks"},
            )

        except Exception as e:
            logger.warning(f"Failed to scrape GSoC: {e}")
            return self._create_gsoc_fallback()

    def _create_gsoc_fallback(self) -> RawOpportunity:
        """Create GSoC opportunity with known data."""
        return RawOpportunity(
            source=self.source_name,
            external_id="oss-gsoc",
            title="Google Summer of Code (GSoC)",
            url="https://summerofcode.withgoogle.com",
            description=(
                "Google Summer of Code is a global program that matches students and beginners "
                "with open source organizations. Contributors work on a 12+ week programming "
                "project under the guidance of mentors. Stipend: $1500-$3000."
            ),
            location="Online",
            is_online=True,
            regions=["Global"],
            total_prize_amount=3000,
            prize_currency="USD",
            tags=["gsoc", "google", "open-source", "mentorship", "students"],
            themes=["open-source", "mentorship", "education"],
            host_name="Google",
            host_url="https://summerofcode.withgoogle.com",
            student_only=True,
        )

    async def _scrape_outreachy(self) -> Optional[RawOpportunity]:
        """Scrape Outreachy internship info."""
        try:
            client = await self.get_client()
            response = await client.get("https://www.outreachy.org")

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")
                desc_elem = soup.select_one("main p, .hero p")
                description = desc_elem.get_text(strip=True)[:1000] if desc_elem else ""

            if not description:
                description = (
                    "Outreachy provides internships in open source and open science. "
                    "Outreachy internships are remote, paid ($7,000), and last three months. "
                    "Focused on supporting diversity in tech."
                )

            return RawOpportunity(
                source=self.source_name,
                external_id="oss-outreachy",
                title="Outreachy Internships",
                url="https://www.outreachy.org",
                description=description,
                location="Online",
                is_online=True,
                regions=["Global"],
                total_prize_amount=7000,
                prize_currency="USD",
                tags=["outreachy", "open-source", "internship", "diversity", "remote"],
                themes=["open-source", "diversity", "internship", "mentorship"],
                host_name="Outreachy",
                host_url="https://www.outreachy.org",
                raw_data={"duration": "3 months", "stipend": "$7,000"},
            )

        except Exception as e:
            logger.warning(f"Failed to scrape Outreachy: {e}")
            return RawOpportunity(
                source=self.source_name,
                external_id="oss-outreachy",
                title="Outreachy Internships",
                url="https://www.outreachy.org",
                description="Paid remote internships in open source ($7,000 for 3 months).",
                location="Online",
                is_online=True,
                regions=["Global"],
                total_prize_amount=7000,
                prize_currency="USD",
                tags=["outreachy", "open-source", "internship", "diversity"],
                themes=["open-source", "diversity", "internship"],
                host_name="Outreachy",
            )

    async def _scrape_open_collective(self) -> List[RawOpportunity]:
        """Scrape Open Collective grant opportunities."""
        opportunities = []

        # Known Open Collective grants/funds
        oc_funds = [
            {
                "id": "oc-opensource-fund",
                "name": "Open Source Collective",
                "url": "https://opencollective.com/opensource",
                "description": "Fiscal host for open source projects. Receive donations, pay contributors, manage funds transparently.",
                "amount": None,
            },
            {
                "id": "oc-webpack-fund",
                "name": "webpack Open Source Fund",
                "url": "https://opencollective.com/webpack",
                "description": "Support webpack development and ecosystem.",
                "amount": None,
            },
            {
                "id": "oc-babel-fund",
                "name": "Babel Open Collective",
                "url": "https://opencollective.com/babel",
                "description": "Support Babel development - the JavaScript compiler.",
                "amount": None,
            },
        ]

        for fund in oc_funds:
            opportunities.append(RawOpportunity(
                source=self.source_name,
                external_id=fund["id"],
                title=fund["name"],
                url=fund["url"],
                description=fund["description"],
                location="Online",
                is_online=True,
                regions=["Global"],
                total_prize_amount=fund["amount"],
                tags=["open-collective", "open-source", "funding", "donations"],
                themes=["open-source", "community-funding"],
                host_name="Open Collective",
                host_url="https://opencollective.com",
            ))

        return opportunities

    def _get_github_sponsors_info(self) -> RawOpportunity:
        """Get GitHub Sponsors Fund info."""
        return RawOpportunity(
            source=self.source_name,
            external_id="oss-github-sponsors",
            title="GitHub Sponsors",
            url="https://github.com/sponsors",
            description=(
                "GitHub Sponsors allows the developer community to financially support the people "
                "and organizations who design, build, and maintain the open source projects they depend on. "
                "GitHub waives payment processing fees for Sponsors payments."
            ),
            location="Online",
            is_online=True,
            regions=["Global"],
            tags=["github", "sponsors", "open-source", "funding", "donations"],
            themes=["open-source", "community-funding", "developer"],
            host_name="GitHub",
            host_url="https://github.com",
            raw_data={"fee": "0% (GitHub covers fees)"},
        )

    def _get_foundation_grants(self) -> List[RawOpportunity]:
        """Get list of foundation grants for open source."""
        grants = [
            {
                "id": "mozilla-moss",
                "name": "Mozilla Open Source Support (MOSS)",
                "url": "https://www.mozilla.org/en-US/moss/",
                "description": "Mozilla awards grants to open source projects that advance the Mozilla mission. Awards range from $5,000 to $150,000.",
                "amount": 50000,
                "host": "Mozilla Foundation",
            },
            {
                "id": "linux-foundation",
                "name": "Linux Foundation Project Support",
                "url": "https://www.linuxfoundation.org/projects",
                "description": "The Linux Foundation hosts critical open source projects and provides funding, governance, and support.",
                "amount": None,
                "host": "Linux Foundation",
            },
            {
                "id": "apache-sponsorship",
                "name": "Apache Software Foundation",
                "url": "https://www.apache.org/foundation/sponsorship.html",
                "description": "The ASF hosts 350+ Apache projects and provides infrastructure, legal, and community support.",
                "amount": None,
                "host": "Apache Software Foundation",
            },
            {
                "id": "nlnet-grants",
                "name": "NLnet Foundation Grants",
                "url": "https://nlnet.nl/propose/",
                "description": "NLnet funds projects that contribute to an open internet. Grants for privacy, security, and open standards projects.",
                "amount": 50000,
                "host": "NLnet Foundation",
            },
            {
                "id": "sovereign-tech-fund",
                "name": "Sovereign Tech Fund",
                "url": "https://sovereigntechfund.de",
                "description": "German government fund for critical open source infrastructure. Large grants for essential projects.",
                "amount": 300000,
                "host": "Sovereign Tech Fund (Germany)",
            },
            {
                "id": "ford-foundation-tech",
                "name": "Ford Foundation Technology Grants",
                "url": "https://www.fordfoundation.org/work/challenging-inequality/technology-and-society/",
                "description": "Grants for technology projects that advance social justice and address inequality.",
                "amount": 100000,
                "host": "Ford Foundation",
            },
            {
                "id": "sloan-foundation",
                "name": "Alfred P. Sloan Foundation Tech Grants",
                "url": "https://sloan.org/programs/digital-technology",
                "description": "Grants for projects advancing data science, open source software, and digital infrastructure.",
                "amount": 150000,
                "host": "Alfred P. Sloan Foundation",
            },
            {
                "id": "python-psf-grants",
                "name": "Python Software Foundation Grants",
                "url": "https://www.python.org/psf/grants/",
                "description": "PSF provides grants for Python development, education, and community building.",
                "amount": 10000,
                "host": "Python Software Foundation",
            },
            {
                "id": "rust-foundation-grants",
                "name": "Rust Foundation Grants",
                "url": "https://foundation.rust-lang.org/grants/",
                "description": "Grants to support Rust development, community events, and project infrastructure.",
                "amount": 20000,
                "host": "Rust Foundation",
            },
            {
                "id": "cncf-grants",
                "name": "CNCF Project Grants",
                "url": "https://www.cncf.io/projects/",
                "description": "Cloud Native Computing Foundation supports cloud-native open source projects with funding and infrastructure.",
                "amount": None,
                "host": "CNCF",
            },
        ]

        return [
            RawOpportunity(
                source=self.source_name,
                external_id=f"oss-{g['id']}",
                title=g["name"],
                url=g["url"],
                description=g["description"],
                location="Online",
                is_online=True,
                regions=["Global"],
                total_prize_amount=g["amount"],
                prize_currency="USD",
                tags=["grant", "open-source", "foundation", "funding"],
                themes=["open-source", "foundation-grant", "community"],
                host_name=g["host"],
                host_url=g["url"],
            )
            for g in grants
        ]

    async def scrape_detail(self, external_id: str, url: str) -> Optional[RawOpportunity]:
        """Scrape detailed grant information."""
        return None


def create_opensource_grants_scraper(**kwargs) -> OpenSourceGrantsScraper:
    """Create an Open Source Grants scraper instance."""
    return OpenSourceGrantsScraper(**kwargs)
