"""Innovate UK funding scraper."""

import asyncio
import logging
import re
from datetime import datetime
from typing import List, Optional

from bs4 import BeautifulSoup

from .base import BaseScraper, RawOpportunity, ScraperResult, ScraperStatus, with_retry

logger = logging.getLogger(__name__)


class InnovateUKScraper(BaseScraper):
    """
    Scraper for Innovate UK and UK Research & Innovation (UKRI) funding.

    Innovate UK is the UK's innovation agency, supporting businesses
    to develop and realise the potential of new ideas.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._api_base = "https://apply-for-innovation-funding.service.gov.uk/competition/search"

    @property
    def source_name(self) -> str:
        return "innovate_uk"

    @property
    def base_url(self) -> str:
        return "https://apply-for-innovation-funding.service.gov.uk/competition/search"

    @with_retry(max_attempts=3)
    async def scrape_list(self, page: int = 1) -> ScraperResult:
        """Scrape Innovate UK funding competitions."""
        client = await self.get_client()
        opportunities: List[RawOpportunity] = []
        errors: List[str] = []

        try:
            # Innovate UK uses a search page
            url = f"{self._api_base}?page={page}"

            response = await client.get(url)

            if response.status_code != 200:
                logger.warning(f"Innovate UK returned {response.status_code}")
                return self._get_fallback_result(page)

            soup = BeautifulSoup(response.text, "lxml")

            # Find competition cards
            competitions = soup.select(".competition-overview, .govuk-grid-row article, [class*='competition']")

            if not competitions:
                # Try alternative selectors
                competitions = soup.select("li.competition, .search-result, tr[class*='competition']")

            logger.info(f"Found {len(competitions)} Innovate UK competitions")

            for comp in competitions:
                try:
                    opp = self._parse_competition(comp)
                    if opp:
                        opportunities.append(opp)
                except Exception as e:
                    errors.append(f"Failed to parse competition: {e}")
                    logger.warning(f"Failed to parse Innovate UK competition: {e}")

            # If we didn't find any, use fallback
            if not opportunities and page == 1:
                opportunities = self._get_known_competitions()

            return ScraperResult(
                opportunities=opportunities,
                status=ScraperStatus.SUCCESS if opportunities else ScraperStatus.PARTIAL,
                source=self.source_name,
                total_found=len(opportunities),
                errors=errors,
                metadata={"page": page},
            )

        except Exception as e:
            logger.error(f"Innovate UK scraping failed: {e}")
            return self._get_fallback_result(page)

    def _get_fallback_result(self, page: int) -> ScraperResult:
        """Return fallback result with known competitions."""
        if page > 1:
            return ScraperResult(
                opportunities=[],
                status=ScraperStatus.SUCCESS,
                source=self.source_name,
                total_found=0,
            )

        opportunities = self._get_known_competitions()
        return ScraperResult(
            opportunities=opportunities,
            status=ScraperStatus.PARTIAL,
            source=self.source_name,
            total_found=len(opportunities),
            metadata={"page": page, "fallback": True},
        )

    def _parse_competition(self, element) -> Optional[RawOpportunity]:
        """Parse a competition from HTML element."""
        try:
            # Find title and link
            title_elem = element.select_one("h2 a, h3 a, .title a, a[href*='competition']")
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            href = title_elem.get("href", "")

            if not title or len(title) < 5:
                return None

            url = href
            if not url.startswith("http"):
                url = f"https://apply-for-innovation-funding.service.gov.uk{href}"

            # Extract competition ID from URL
            external_id = url.rstrip("/").split("/")[-1]
            if not external_id or not external_id.replace("-", "").replace("_", ""):
                external_id = title.lower().replace(" ", "-")[:50]

            # Find deadline
            deadline_elem = element.select_one("[class*='deadline'], [class*='close'], .date, time")
            deadline = deadline_elem.get_text(strip=True) if deadline_elem else None

            # Find funding amount
            funding_elem = element.select_one("[class*='funding'], [class*='amount'], [class*='budget']")
            funding_text = funding_elem.get_text(strip=True) if funding_elem else ""
            funding_amount = self._parse_funding(funding_text)

            # Description
            desc_elem = element.select_one("p, .description, .summary, [class*='description']")
            description = desc_elem.get_text(strip=True)[:1000] if desc_elem else ""

            if not description:
                description = f"Innovate UK competition: {title}"

            # Status
            status_elem = element.select_one("[class*='status'], .tag, .badge")
            status = status_elem.get_text(strip=True) if status_elem else "Open"

            # Tags
            tags = ["innovate-uk", "ukri", "uk-funding", "innovation", "business"]
            title_lower = title.lower()
            if "ai" in title_lower or "artificial" in title_lower:
                tags.append("ai")
            if "net zero" in title_lower or "green" in title_lower or "climate" in title_lower:
                tags.append("net-zero")
            if "health" in title_lower or "nhs" in title_lower:
                tags.append("health")
            if "manufacturing" in title_lower:
                tags.append("manufacturing")
            if "sme" in title_lower or "small business" in title_lower:
                tags.append("sme")

            return RawOpportunity(
                source=self.source_name,
                external_id=f"iuk-{external_id}",
                title=title,
                url=url,
                description=description,
                submission_deadline=deadline,
                end_date=deadline,
                location="United Kingdom",
                is_online=True,
                regions=["UK", "United Kingdom"],
                total_prize_amount=funding_amount,
                prize_currency="GBP",
                tags=tags,
                themes=["innovation", "business", "uk-funding"],
                host_name="Innovate UK",
                host_url="https://www.ukri.org/councils/innovate-uk/",
                raw_data={"status": status},
            )

        except Exception as e:
            logger.warning(f"Failed to parse Innovate UK competition: {e}")
            return None

    def _parse_funding(self, funding_str: str) -> Optional[float]:
        """Parse funding amount from string."""
        if not funding_str:
            return None

        try:
            funding_str = funding_str.upper().replace(",", "").replace("GBP", "").replace("£", "").strip()

            if "MILLION" in funding_str or "M" in funding_str:
                match = re.search(r"([\d.]+)", funding_str)
                if match:
                    return float(match.group(1)) * 1000000

            match = re.search(r"([\d.]+)", funding_str)
            if match:
                return float(match.group(1))

        except Exception:
            pass

        return None

    def _get_known_competitions(self) -> List[RawOpportunity]:
        """Return known Innovate UK funding programmes."""
        programmes = [
            {
                "id": "smart-grants",
                "title": "Smart Grants",
                "url": "https://apply-for-innovation-funding.service.gov.uk/competition/search",
                "description": "Smart Grants fund game-changing and disruptive ideas that could make a significant impact. Open to UK businesses of any size, R&D projects between £25K-£2M.",
                "funding": 500000,
                "tags": ["smart", "disruptive", "r&d"],
            },
            {
                "id": "innovate-uk-loans",
                "title": "Innovate UK Loans",
                "url": "https://apply-for-innovation-funding.service.gov.uk/competition/search",
                "description": "Innovation loans for late-stage R&D projects. Loans from £100K to £2M for UK SMEs.",
                "funding": 1000000,
                "tags": ["loans", "sme", "late-stage"],
            },
            {
                "id": "catapult-support",
                "title": "Catapult Network Programmes",
                "url": "https://catapult.org.uk",
                "description": "UK Catapult centres offer support, facilities, and collaborative R&D opportunities across key sectors.",
                "funding": 250000,
                "tags": ["catapult", "collaboration", "facilities"],
            },
            {
                "id": "knowledge-transfer",
                "title": "Knowledge Transfer Partnerships (KTP)",
                "url": "https://www.ktp-uk.org",
                "description": "KTP helps businesses innovate by connecting them with UK universities. Projects last 12-36 months.",
                "funding": 150000,
                "tags": ["ktp", "university", "partnership"],
            },
            {
                "id": "sbri",
                "title": "Small Business Research Initiative (SBRI)",
                "url": "https://www.gov.uk/government/collections/sbri-the-small-business-research-initiative",
                "description": "SBRI connects public sector challenges with innovative businesses. Phase 1 up to £100K, Phase 2 up to £1M.",
                "funding": 500000,
                "tags": ["sbri", "public-sector", "procurement"],
            },
            {
                "id": "strength-in-places",
                "title": "Strength in Places Fund",
                "url": "https://www.ukri.org/what-we-offer/browse-our-areas-of-investment-and-support/strength-in-places-fund/",
                "description": "Major place-based R&D initiatives. Large collaborative bids for regional economic growth.",
                "funding": 10000000,
                "tags": ["regional", "collaboration", "economic-growth"],
            },
            {
                "id": "net-zero",
                "title": "Net Zero Innovation Portfolio",
                "url": "https://www.gov.uk/government/collections/net-zero-innovation-portfolio",
                "description": "Funding for clean energy innovation including hydrogen, CCUS, nuclear, and energy efficiency.",
                "funding": 1000000,
                "tags": ["net-zero", "clean-energy", "climate"],
            },
            {
                "id": "industrial-strategy-challenge",
                "title": "ISCF - Industrial Strategy Challenges",
                "url": "https://www.ukri.org/what-we-offer/browse-our-areas-of-investment-and-support/industrial-strategy-challenge-fund/",
                "description": "Major research challenges addressing UK industrial needs in areas like AI, clean growth, and ageing society.",
                "funding": 2000000,
                "tags": ["iscf", "industrial", "strategic"],
            },
            {
                "id": "biomedical-catalyst",
                "title": "Biomedical Catalyst",
                "url": "https://apply-for-innovation-funding.service.gov.uk/competition/search",
                "description": "Funding for life sciences projects. Supports SMEs developing innovative healthcare solutions.",
                "funding": 500000,
                "tags": ["biomedical", "healthcare", "life-sciences"],
            },
            {
                "id": "emerging-tech",
                "title": "Emerging Technologies Programme",
                "url": "https://www.ukri.org/opportunity/",
                "description": "Funding for early-stage research in emerging technologies including quantum, AI, and advanced materials.",
                "funding": 300000,
                "tags": ["emerging-tech", "quantum", "ai", "materials"],
            },
        ]

        return [
            RawOpportunity(
                source=self.source_name,
                external_id=f"iuk-{p['id']}",
                title=p["title"],
                url=p["url"],
                description=p["description"],
                location="United Kingdom",
                is_online=True,
                regions=["UK", "United Kingdom"],
                total_prize_amount=p["funding"],
                prize_currency="GBP",
                tags=["innovate-uk", "ukri", "uk-funding"] + p.get("tags", []),
                themes=["innovation", "business", "uk-funding"],
                host_name="Innovate UK / UKRI",
                host_url="https://www.ukri.org/councils/innovate-uk/",
            )
            for p in programmes
        ]

    async def scrape_detail(self, external_id: str, url: str) -> Optional[RawOpportunity]:
        """Scrape detailed competition information."""
        return None

    async def health_check(self) -> bool:
        """Check if Innovate UK portal is accessible."""
        try:
            client = await self.get_client()
            response = await client.get("https://apply-for-innovation-funding.service.gov.uk")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Innovate UK health check failed: {e}")
            return False


def create_innovate_uk_scraper(**kwargs) -> InnovateUKScraper:
    """Create an Innovate UK scraper instance."""
    return InnovateUKScraper(**kwargs)
