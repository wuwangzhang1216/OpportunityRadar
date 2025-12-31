"""SBIR/STTR scraper for US small business innovation research funding."""

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


class SBIRScraper(BaseScraper):
    """
    Scraper for SBIR.gov - Small Business Innovation Research/STTR programs.

    SBIR/STTR are competitive programs that encourage small businesses to engage
    in Federal Research/Research and Development with commercialization potential.
    """

    # SBIR phases
    PHASES = {
        "phase1": "Phase I - Feasibility",
        "phase2": "Phase II - Development",
        "phase3": "Phase III - Commercialization",
    }

    def __init__(self, headless: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.headless = headless
        self._browser: Optional["Browser"] = None
        self._playwright = None

    @property
    def source_name(self) -> str:
        return "sbir"

    @property
    def base_url(self) -> str:
        return "https://www.sbir.gov/solicitations/open"

    async def _get_browser(self) -> "Browser":
        """Get or create Playwright browser instance."""
        if self._browser is None or not self._browser.is_connected():
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
            )
            logger.info("SBIR: Playwright browser launched")

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
        """Scrape SBIR/STTR solicitations."""
        opportunities: List[RawOpportunity] = []
        errors: List[str] = []
        browser_page = None

        try:
            browser_page = await self._create_page()

            # Navigate to open solicitations
            url = f"{self.base_url}?page={page - 1}"  # 0-indexed
            logger.info(f"Navigating to SBIR: {url}")
            await browser_page.goto(url, wait_until="networkidle", timeout=60000)

            # Wait for content
            await browser_page.wait_for_timeout(3000)

            html_content = await browser_page.content()
            soup = BeautifulSoup(html_content, "lxml")

            # Find solicitation cards/rows
            solicitations = soup.select(".views-row, .solicitation-row, tr.odd, tr.even")

            if not solicitations:
                # Try alternative selectors
                solicitations = soup.select("[class*='solicitation'], .node--type-solicitation")

            logger.info(f"Found {len(solicitations)} SBIR solicitations")

            for sol in solicitations:
                try:
                    opp = self._parse_solicitation(sol)
                    if opp:
                        opportunities.append(opp)
                except Exception as e:
                    errors.append(f"Failed to parse solicitation: {e}")
                    logger.warning(f"Failed to parse SBIR solicitation: {e}")

            # Also try to parse from API if available
            api_opps = await self._scrape_api(page)
            if api_opps:
                # Deduplicate by external_id
                existing_ids = {o.external_id for o in opportunities}
                for opp in api_opps:
                    if opp.external_id not in existing_ids:
                        opportunities.append(opp)

            return ScraperResult(
                opportunities=opportunities,
                status=ScraperStatus.SUCCESS if opportunities else ScraperStatus.PARTIAL,
                source=self.source_name,
                total_found=len(opportunities),
                errors=errors,
                metadata={"page": page},
            )

        except Exception as e:
            logger.error(f"SBIR scraping failed: {e}")
            import traceback
            traceback.print_exc()
            return ScraperResult(
                opportunities=[],
                status=ScraperStatus.FAILED,
                source=self.source_name,
                error_message=str(e),
            )
        finally:
            if browser_page:
                try:
                    await browser_page.context.close()
                except Exception:
                    pass

    async def _scrape_api(self, page: int = 1) -> List[RawOpportunity]:
        """Try to scrape from SBIR API endpoint."""
        opportunities = []

        try:
            client = await self.get_client()

            # SBIR public API endpoint (docs: https://www.sbir.gov/api/solicitation)
            # Format: https://api.www.sbir.gov/public/api/solicitations?open=1&rows=50
            api_url = f"https://api.www.sbir.gov/public/api/solicitations?open=1&rows=50&start={((page - 1) * 50)}"

            response = await client.get(api_url, headers={"Accept": "application/json"})

            if response.status_code == 200:
                data = response.json()
                sols = data if isinstance(data, list) else data.get("data", []) or data.get("solicitations", [])

                logger.info(f"SBIR API returned {len(sols)} solicitations")

                for sol in sols:
                    opp = self._parse_api_solicitation(sol)
                    if opp:
                        opportunities.append(opp)
            else:
                logger.warning(f"SBIR API returned {response.status_code}")

                # Try alternative XML endpoint
                xml_url = f"https://api.www.sbir.gov/public/api/solicitations?open=1&format=xml&rows=50"
                xml_response = await client.get(xml_url)

                if xml_response.status_code == 200:
                    # Parse XML response
                    opportunities.extend(self._parse_xml_response(xml_response.text))

        except Exception as e:
            logger.debug(f"SBIR API scrape failed (falling back to HTML): {e}")

        # Return known SBIR programs as fallback if no results
        if not opportunities and page == 1:
            logger.info("Using known SBIR programs as fallback")
            opportunities = self._get_known_sbir_programs()

        return opportunities

    def _parse_xml_response(self, xml_text: str) -> List[RawOpportunity]:
        """Parse SBIR XML response."""
        opportunities = []
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(xml_text, "xml")

            for sol in soup.find_all("solicitation"):
                try:
                    title = sol.find("solicitation_title")
                    title = title.get_text(strip=True) if title else None
                    if not title:
                        continue

                    sol_num = sol.find("solicitation_number")
                    sol_num = sol_num.get_text(strip=True) if sol_num else ""

                    agency = sol.find("agency")
                    agency = agency.get_text(strip=True) if agency else "Federal Agency"

                    close_date = sol.find("close_date")
                    close_date = close_date.get_text(strip=True) if close_date else None

                    link = sol.find("sbir_solicitation_link")
                    url = link.get_text(strip=True) if link else f"https://www.sbir.gov/solicitations/open"

                    phase = sol.find("phase")
                    phase = phase.get_text(strip=True) if phase else ""

                    # Estimate prize based on phase
                    prize_amount = 275000 if "1" in phase or "I" in phase.upper() else 1000000

                    opportunities.append(RawOpportunity(
                        source=self.source_name,
                        external_id=f"sbir-{sol_num or title[:30].replace(' ', '-')}",
                        title=title,
                        url=url,
                        description=f"SBIR/STTR {phase} solicitation from {agency}",
                        submission_deadline=close_date,
                        end_date=close_date,
                        location="United States",
                        is_online=True,
                        regions=["US"],
                        total_prize_amount=prize_amount,
                        prize_currency="USD",
                        tags=["sbir", "sttr", "federal-funding", "small-business"],
                        themes=["innovation", "research", "government-funding"],
                        host_name=agency,
                        host_url="https://www.sbir.gov",
                    ))
                except Exception as e:
                    logger.debug(f"Failed to parse SBIR XML solicitation: {e}")

        except Exception as e:
            logger.warning(f"Failed to parse SBIR XML: {e}")

        return opportunities

    def _get_known_sbir_programs(self) -> List[RawOpportunity]:
        """Return known SBIR/STTR programs as fallback."""
        programs = [
            {
                "id": "dod-sbir",
                "title": "DoD SBIR/STTR Program",
                "agency": "Department of Defense",
                "description": "Largest SBIR program. Phase I: $50K-$275K, Phase II: $750K-$1.8M. Covers defense technology.",
                "amount": 275000,
                "url": "https://www.dodsbirsttr.mil/",
            },
            {
                "id": "hhs-sbir",
                "title": "HHS/NIH SBIR/STTR Program",
                "agency": "Department of Health and Human Services",
                "description": "Health and biomedical research innovation. Phase I: $275K, Phase II: $2M.",
                "amount": 275000,
                "url": "https://sbir.nih.gov/",
            },
            {
                "id": "nsf-sbir",
                "title": "NSF SBIR/STTR Program",
                "agency": "National Science Foundation",
                "description": "Deep technology startups. Phase I: $275K, Phase II: $1M.",
                "amount": 275000,
                "url": "https://seedfund.nsf.gov/",
            },
            {
                "id": "doe-sbir",
                "title": "DOE SBIR/STTR Program",
                "agency": "Department of Energy",
                "description": "Energy technology innovation. Phase I: $275K, Phase II: $1.8M.",
                "amount": 275000,
                "url": "https://www.sbir.gov/agencies/department-energy",
            },
            {
                "id": "nasa-sbir",
                "title": "NASA SBIR/STTR Program",
                "agency": "NASA",
                "description": "Space technology and aeronautics. Phase I: $150K, Phase II: $850K.",
                "amount": 150000,
                "url": "https://sbir.nasa.gov/",
            },
            {
                "id": "usda-sbir",
                "title": "USDA SBIR Program",
                "agency": "USDA",
                "description": "Agricultural innovation. Phase I: $100K, Phase II: $600K.",
                "amount": 100000,
                "url": "https://www.sbir.gov/agencies/department-agriculture",
            },
            {
                "id": "epa-sbir",
                "title": "EPA SBIR Program",
                "agency": "Environmental Protection Agency",
                "description": "Environmental technology solutions. Phase I: $100K, Phase II: $400K.",
                "amount": 100000,
                "url": "https://www.epa.gov/sbir",
            },
            {
                "id": "dhs-sbir",
                "title": "DHS SBIR Program",
                "agency": "Department of Homeland Security",
                "description": "Homeland security technology. Phase I: $150K, Phase II: $1M.",
                "amount": 150000,
                "url": "https://www.sbir.gov/agencies/department-homeland-security",
            },
        ]

        return [
            RawOpportunity(
                source=self.source_name,
                external_id=f"sbir-{p['id']}",
                title=p["title"],
                url=p["url"],
                description=p["description"],
                location="United States",
                is_online=True,
                regions=["US"],
                total_prize_amount=p["amount"],
                prize_currency="USD",
                tags=["sbir", "sttr", "federal-funding", "small-business", "innovation"],
                themes=["innovation", "research", "government-funding", "startup"],
                host_name=p["agency"],
                host_url="https://www.sbir.gov",
            )
            for p in programs
        ]

    def _parse_solicitation(self, element) -> Optional[RawOpportunity]:
        """Parse a solicitation from HTML element."""
        try:
            # Find title and link
            title_elem = element.select_one("h3 a, h2 a, .title a, a[href*='node']")
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            href = title_elem.get("href", "")
            url = href if href.startswith("http") else f"https://www.sbir.gov{href}"

            # Extract ID from URL
            external_id = url.rstrip("/").split("/")[-1]
            if not external_id or external_id == "solicitations":
                return None

            # Find agency
            agency_elem = element.select_one(".agency, .field--name-field-agency, [class*='agency']")
            agency = agency_elem.get_text(strip=True) if agency_elem else "Federal Agency"

            # Find phase
            phase_elem = element.select_one(".phase, .field--name-field-phase, [class*='phase']")
            phase = phase_elem.get_text(strip=True) if phase_elem else ""

            # Find deadline
            deadline_elem = element.select_one(".deadline, .close-date, [class*='deadline'], [class*='close']")
            deadline = deadline_elem.get_text(strip=True) if deadline_elem else None

            # Find topic areas
            topics_elem = element.select_one(".topics, .field--name-field-topics, [class*='topic']")
            topics = topics_elem.get_text(strip=True) if topics_elem else ""

            # Build description
            desc_elem = element.select_one(".description, .summary, .field--name-body, p")
            description = desc_elem.get_text(strip=True)[:1000] if desc_elem else ""

            if not description:
                description = f"SBIR/STTR {phase} solicitation from {agency}"
            if topics:
                description += f"\n\nTopics: {topics}"

            # Estimate prize based on phase
            prize_amount = None
            if "phase i" in phase.lower() or "phase 1" in phase.lower():
                prize_amount = 275000  # Typical Phase I
            elif "phase ii" in phase.lower() or "phase 2" in phase.lower():
                prize_amount = 1000000  # Typical Phase II

            # Tags
            tags = ["sbir", "sttr", "small-business", "innovation", "federal-funding"]
            if agency:
                tags.append(agency.lower().replace(" ", "-")[:30])
            if phase:
                tags.append(phase.lower().replace(" ", "-")[:20])

            return RawOpportunity(
                source=self.source_name,
                external_id=f"sbir-{external_id}",
                title=title,
                url=url,
                description=description,
                submission_deadline=deadline,
                end_date=deadline,
                location="United States",
                is_online=True,
                regions=["US"],
                total_prize_amount=prize_amount,
                prize_currency="USD",
                tags=tags,
                themes=["innovation", "research", "small-business", "government-funding"],
                host_name=agency,
                host_url="https://www.sbir.gov",
                raw_data={"phase": phase, "topics": topics},
            )

        except Exception as e:
            logger.warning(f"Failed to parse SBIR solicitation: {e}")
            return None

    def _parse_api_solicitation(self, data: dict) -> Optional[RawOpportunity]:
        """Parse solicitation from API response."""
        try:
            sol_id = data.get("id") or data.get("nid")
            if not sol_id:
                return None

            title = data.get("title", "SBIR Solicitation")
            url = data.get("url") or f"https://www.sbir.gov/node/{sol_id}"
            if not url.startswith("http"):
                url = f"https://www.sbir.gov{url}"

            agency = data.get("agency") or data.get("agency_name", "Federal Agency")
            phase = data.get("phase", "")
            deadline = data.get("close_date") or data.get("deadline")

            description = data.get("description") or data.get("summary", "")
            if not description:
                description = f"SBIR/STTR solicitation from {agency}"

            # Prize estimation
            prize_amount = None
            if "1" in str(phase) or "I" in str(phase).upper():
                prize_amount = 275000
            elif "2" in str(phase) or "II" in str(phase).upper():
                prize_amount = 1000000

            tags = ["sbir", "sttr", "federal-funding", "innovation"]

            return RawOpportunity(
                source=self.source_name,
                external_id=f"sbir-{sol_id}",
                title=title,
                url=url,
                description=description[:2000],
                submission_deadline=deadline,
                end_date=deadline,
                location="United States",
                is_online=True,
                regions=["US"],
                total_prize_amount=prize_amount,
                prize_currency="USD",
                tags=tags,
                themes=["innovation", "research", "government-funding"],
                host_name=agency,
                host_url="https://www.sbir.gov",
                raw_data=data,
            )

        except Exception as e:
            logger.warning(f"Failed to parse SBIR API data: {e}")
            return None

    async def scrape_detail(self, external_id: str, url: str) -> Optional[RawOpportunity]:
        """Scrape detailed solicitation information."""
        try:
            client = await self.get_client()
            response = await client.get(url)

            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, "lxml")

            # Extract details from page
            title_elem = soup.select_one("h1, .page-title")
            title = title_elem.get_text(strip=True) if title_elem else external_id

            body_elem = soup.select_one(".field--name-body, .content, article")
            description = body_elem.get_text(strip=True)[:3000] if body_elem else ""

            return RawOpportunity(
                source=self.source_name,
                external_id=external_id,
                title=title,
                url=url,
                description=description,
                location="United States",
                is_online=True,
                regions=["US"],
                tags=["sbir", "sttr", "federal-funding"],
                host_name="US Federal Government",
                host_url="https://www.sbir.gov",
            )

        except Exception as e:
            logger.error(f"Failed to scrape SBIR detail: {e}")
            return None


def create_sbir_scraper(**kwargs) -> SBIRScraper:
    """Create an SBIR scraper instance."""
    return SBIRScraper(**kwargs)
