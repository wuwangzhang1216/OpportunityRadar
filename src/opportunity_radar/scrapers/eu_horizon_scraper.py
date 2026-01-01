"""EU Horizon Europe funding scraper."""

import asyncio
import logging
import re
from datetime import datetime
from typing import List, Optional

from .base import BaseScraper, RawOpportunity, ScraperResult, ScraperStatus, with_retry

logger = logging.getLogger(__name__)


class EUHorizonScraper(BaseScraper):
    """
    Scraper for EU Horizon Europe funding opportunities.

    Horizon Europe is the EU's key funding programme for research and innovation.
    Uses the EU Funding & Tenders Portal API.
    """

    # Programme types relevant to tech/innovation
    PROGRAMME_TYPES = [
        "HORIZON",  # Horizon Europe
        "DIGITAL",  # Digital Europe Programme
        "EIC",      # European Innovation Council
    ]

    def __init__(self, programme_types: Optional[List[str]] = None, **kwargs):
        super().__init__(**kwargs)
        self.programme_types = programme_types or self.PROGRAMME_TYPES
        # EU Funding & Tenders Portal data endpoint
        self._api_base = "https://ec.europa.eu/info/funding-tenders/opportunities/data/topicSearch.json"

    @property
    def source_name(self) -> str:
        return "eu_horizon"

    @property
    def base_url(self) -> str:
        return "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-search"

    @with_retry(max_attempts=3)
    async def scrape_list(self, page: int = 1) -> ScraperResult:
        """Scrape EU funding opportunities."""
        client = await self.get_client()
        opportunities: List[RawOpportunity] = []
        errors: List[str] = []

        try:
            # Try multiple EU funding data endpoints
            endpoints_to_try = [
                # EU Funding Portal (new domain after redirect)
                "https://commission.europa.eu/funding-tenders/find-funding/eu-funding-programmes/horizon-europe_en",
                # EIC funding page
                "https://eic.ec.europa.eu/eic-funding-opportunities_en",
                # EU Portal topic search
                "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-search",
            ]

            data = None
            for endpoint in endpoints_to_try:
                try:
                    # Try scraping HTML page (all endpoints are now HTML)
                    response = await client.get(
                        endpoint,
                        timeout=30.0,
                        follow_redirects=True,
                    )
                    if response.status_code == 200:
                        html_opps = await self._parse_html_topics(response.text)
                        if html_opps:
                            opportunities.extend(html_opps)
                            logger.info(f"EU Horizon: Found {len(html_opps)} opportunities from {endpoint}")
                            break
                except Exception as e:
                    logger.debug(f"EU endpoint {endpoint} failed: {e}")
                    continue

            # If scraping didn't work well, supplement with known programmes
            if len(opportunities) < 5:
                fallback_opps = self._get_known_programmes()
                existing_ids = {o.external_id for o in opportunities}
                for opp in fallback_opps:
                    if opp.external_id not in existing_ids:
                        opportunities.append(opp)

            return ScraperResult(
                opportunities=opportunities,
                status=ScraperStatus.SUCCESS if len(opportunities) > 10 else ScraperStatus.PARTIAL,
                source=self.source_name,
                total_found=len(opportunities),
                errors=errors,
                metadata={"page": page},
            )

        except Exception as e:
            logger.error(f"EU Horizon scraping failed: {e}")
            return await self._scrape_fallback(page)

    async def _parse_html_topics(self, html: str) -> List[RawOpportunity]:
        """Parse topics from HTML page."""
        opportunities = []
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")

            # Look for topic cards/items
            topic_elements = soup.select(
                "[class*='topic'], [class*='call'], [class*='opportunity'], "
                "article, .search-result, tr[data-topic]"
            )

            for elem in topic_elements[:50]:
                try:
                    title_elem = elem.select_one("h2 a, h3 a, .title a, a[href*='topic']")
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    href = title_elem.get("href", "")

                    if not title or len(title) < 10:
                        continue

                    url = href
                    if not url.startswith("http"):
                        url = f"https://ec.europa.eu{href}"

                    # Extract topic ID from URL
                    topic_id = url.rstrip("/").split("/")[-1]
                    if not topic_id:
                        topic_id = title[:40].lower().replace(" ", "-")

                    # Find deadline
                    deadline_elem = elem.select_one("[class*='deadline'], [class*='date'], time")
                    deadline = deadline_elem.get_text(strip=True) if deadline_elem else None

                    # Find budget
                    budget_elem = elem.select_one("[class*='budget'], [class*='amount']")
                    budget = self._parse_budget(budget_elem.get_text(strip=True)) if budget_elem else None

                    opportunities.append(RawOpportunity(
                        source=self.source_name,
                        external_id=f"eu-{topic_id}",
                        title=title,
                        url=url,
                        description=f"EU Horizon Europe funding opportunity: {title}",
                        submission_deadline=deadline,
                        end_date=deadline,
                        location="European Union",
                        is_online=True,
                        regions=["EU", "Europe"],
                        total_prize_amount=budget,
                        prize_currency="EUR",
                        tags=["eu-funding", "horizon-europe", "europe", "research"],
                        themes=["research", "innovation", "eu-funding"],
                        host_name="European Commission",
                        host_url="https://ec.europa.eu",
                    ))
                except Exception as e:
                    logger.debug(f"Failed to parse EU HTML topic: {e}")

        except Exception as e:
            logger.warning(f"Failed to parse EU HTML: {e}")

        return opportunities

    async def _scrape_fallback(self, page: int = 1) -> ScraperResult:
        """Fallback to known programmes."""
        if page > 1:
            return ScraperResult(
                opportunities=[],
                status=ScraperStatus.SUCCESS,
                source=self.source_name,
                total_found=0,
            )

        opportunities = self._get_known_programmes()

        return ScraperResult(
            opportunities=opportunities,
            status=ScraperStatus.PARTIAL,
            source=self.source_name,
            total_found=len(opportunities),
            metadata={"page": page, "fallback": True},
        )

    def _parse_topic(self, data: dict) -> Optional[RawOpportunity]:
        """Parse a topic from API response."""
        try:
            topic_id = data.get("identifier") or data.get("topicId")
            if not topic_id:
                return None

            title = data.get("title") or data.get("topicTitle", "EU Funding Opportunity")

            # Build URL
            url = f"https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/{topic_id}"

            # Parse dates
            deadline = data.get("deadlineDate") or data.get("deadline")
            open_date = data.get("openDate") or data.get("publicationDate")

            # Parse budget
            budget_str = data.get("budget") or data.get("indicativeBudget", "")
            budget = self._parse_budget(budget_str)

            # Description
            description_parts = []
            if data.get("description"):
                description_parts.append(data["description"][:1500])
            if data.get("programmeName"):
                description_parts.append(f"Programme: {data['programmeName']}")
            if data.get("callTitle"):
                description_parts.append(f"Call: {data['callTitle']}")

            description = "\n".join(description_parts) if description_parts else f"EU funding opportunity: {title}"

            # Programme info
            programme = data.get("programmeName", "") or data.get("programme", "")

            # Tags
            tags = ["eu-funding", "horizon-europe", "europe", "research", "innovation"]
            if "digital" in programme.lower():
                tags.extend(["digital", "technology"])
            if "eic" in programme.lower():
                tags.extend(["eic", "startup", "scale-up"])
            if "green" in title.lower() or "climate" in title.lower():
                tags.append("green-deal")
            if "health" in title.lower():
                tags.append("health")
            if "ai" in title.lower() or "artificial" in title.lower():
                tags.append("ai")

            return RawOpportunity(
                source=self.source_name,
                external_id=f"eu-{topic_id}",
                title=title,
                url=url,
                description=description[:3000],
                start_date=open_date,
                end_date=deadline,
                submission_deadline=deadline,
                location="European Union",
                is_online=True,
                regions=["EU", "Europe"],
                total_prize_amount=budget,
                prize_currency="EUR",
                tags=tags,
                themes=["research", "innovation", "eu-funding"],
                host_name="European Commission",
                host_url="https://ec.europa.eu",
                raw_data=data,
            )

        except Exception as e:
            logger.warning(f"Failed to parse EU topic: {e}")
            return None

    def _parse_budget(self, budget_str) -> Optional[float]:
        """Parse budget amount from string."""
        if not budget_str:
            return None

        try:
            if isinstance(budget_str, (int, float)):
                return float(budget_str)

            # Handle strings like "EUR 10 million" or "10,000,000"
            budget_str = str(budget_str).upper()
            budget_str = budget_str.replace("EUR", "").replace(",", "").strip()

            if "MILLION" in budget_str or "M" in budget_str:
                match = re.search(r"([\d.]+)", budget_str)
                if match:
                    return float(match.group(1)) * 1000000
            elif "BILLION" in budget_str or "B" in budget_str:
                match = re.search(r"([\d.]+)", budget_str)
                if match:
                    return float(match.group(1)) * 1000000000
            else:
                match = re.search(r"([\d.]+)", budget_str)
                if match:
                    return float(match.group(1))

        except Exception:
            pass

        return None

    def _get_known_programmes(self) -> List[RawOpportunity]:
        """Return known EU funding programmes."""
        programmes = [
            {
                "id": "eic-accelerator",
                "title": "EIC Accelerator",
                "url": "https://eic.ec.europa.eu/eic-funding-opportunities/eic-accelerator_en",
                "description": "The EIC Accelerator supports startups and SMEs to scale up innovations. Grants up to EUR 2.5 million + equity up to EUR 15 million.",
                "budget": 2500000,
                "tags": ["eic", "startup", "scale-up", "equity"],
            },
            {
                "id": "eic-pathfinder",
                "title": "EIC Pathfinder",
                "url": "https://eic.ec.europa.eu/eic-funding-opportunities/eic-pathfinder_en",
                "description": "The EIC Pathfinder supports collaborative research to develop breakthrough technologies. Grants up to EUR 4 million.",
                "budget": 4000000,
                "tags": ["eic", "research", "breakthrough", "deep-tech"],
            },
            {
                "id": "eic-transition",
                "title": "EIC Transition",
                "url": "https://eic.ec.europa.eu/eic-funding-opportunities/eic-transition_en",
                "description": "EIC Transition helps mature research results into innovations. Grants up to EUR 2.5 million.",
                "budget": 2500000,
                "tags": ["eic", "transition", "commercialization"],
            },
            {
                "id": "digital-europe",
                "title": "Digital Europe Programme",
                "url": "https://digital-strategy.ec.europa.eu/en/activities/digital-programme",
                "description": "Digital Europe Programme supports digital transformation with focus on AI, cybersecurity, advanced digital skills, and digital public services.",
                "budget": 1000000,
                "tags": ["digital", "ai", "cybersecurity", "skills"],
            },
            {
                "id": "horizon-msca",
                "title": "Marie Sklodowska-Curie Actions (MSCA)",
                "url": "https://marie-sklodowska-curie-actions.ec.europa.eu",
                "description": "MSCA funds researchers at all career stages. Includes postdoctoral fellowships, doctoral networks, and staff exchanges.",
                "budget": 200000,
                "tags": ["msca", "research", "fellowship", "doctoral", "postdoc"],
            },
            {
                "id": "horizon-erc",
                "title": "European Research Council (ERC) Grants",
                "url": "https://erc.europa.eu/funding",
                "description": "ERC funds frontier research. Starting Grants (up to EUR 1.5M), Consolidator Grants (up to EUR 2M), Advanced Grants (up to EUR 2.5M).",
                "budget": 2000000,
                "tags": ["erc", "research", "frontier", "excellence"],
            },
            {
                "id": "cascade-funding",
                "title": "Cascade Funding / Open Calls",
                "url": "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-search",
                "description": "Various EU projects offer cascade funding (sub-grants) for SMEs and startups through open calls. Typically EUR 50K-200K.",
                "budget": 100000,
                "tags": ["cascade", "sme", "startup", "sub-grant"],
            },
            {
                "id": "eurostars",
                "title": "Eurostars Programme",
                "url": "https://www.eurekanetwork.org/programmes/eurostars",
                "description": "Eurostars funds international R&D projects led by innovative SMEs. Projects of 2-3 years, funding varies by country.",
                "budget": 500000,
                "tags": ["eurostars", "sme", "r&d", "international"],
            },
            {
                "id": "eureka-clusters",
                "title": "EUREKA Clusters",
                "url": "https://www.eurekanetwork.org/countries/",
                "description": "EUREKA Clusters fund collaborative R&D in specific technology domains including AI, digital manufacturing, and more.",
                "budget": 1000000,
                "tags": ["eureka", "clusters", "r&d", "collaboration"],
            },
            {
                "id": "ngeu-rrf",
                "title": "NextGenerationEU / Recovery Fund",
                "url": "https://next-generation-eu.europa.eu",
                "description": "EUR 750 billion recovery fund with significant allocations for digital transition and green investments.",
                "budget": 5000000,
                "tags": ["nextgen", "recovery", "digital", "green"],
            },
        ]

        return [
            RawOpportunity(
                source=self.source_name,
                external_id=f"eu-{p['id']}",
                title=p["title"],
                url=p["url"],
                description=p["description"],
                location="European Union",
                is_online=True,
                regions=["EU", "Europe"],
                total_prize_amount=p["budget"],
                prize_currency="EUR",
                tags=["eu-funding", "horizon-europe"] + p.get("tags", []),
                themes=["research", "innovation", "eu-funding"],
                host_name="European Commission",
                host_url="https://ec.europa.eu",
            )
            for p in programmes
        ]

    @with_retry(max_attempts=3)
    async def scrape_detail(self, external_id: str, url: str) -> Optional[RawOpportunity]:
        """Scrape detailed EU funding topic information."""
        # Extract topic ID from external_id (format: eu-{id})
        topic_id = external_id.replace("eu-", "")

        try:
            client = await self.get_client()

            # Fetch the detail page
            response = await client.get(url, timeout=30.0, follow_redirects=True)

            if response.status_code != 200:
                logger.warning(f"EU Horizon detail page returned {response.status_code}")
                return None

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, "lxml")

            return self._parse_detail_page(soup, topic_id, url)

        except Exception as e:
            logger.error(f"Failed to scrape EU Horizon detail for {topic_id}: {e}")
            return None

    def _parse_detail_page(self, soup, topic_id: str, url: str) -> Optional[RawOpportunity]:
        """Parse detailed EU funding page."""
        try:
            # Title - try multiple selectors
            title = None
            for selector in ["h1", ".page-title", "[class*='title']", "title"]:
                elem = soup.select_one(selector)
                if elem:
                    title = elem.get_text(strip=True)
                    if title and len(title) > 5:
                        break

            if not title:
                title = f"EU Funding Opportunity: {topic_id}"

            # Clean up title (remove site name suffixes)
            for suffix in [" | European Commission", " - European Commission", " | EIC"]:
                if suffix in title:
                    title = title.split(suffix)[0].strip()

            # Description - gather from multiple sections
            description_parts = []

            # Main content area
            content_selectors = [
                "article",
                ".field--name-body",
                ".content-body",
                "#main-content",
                ".page-content",
                "[class*='description']",
                "[class*='content']",
            ]

            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Get text but skip navigation/menu items
                    for nav in content_elem.select("nav, .menu, .breadcrumb, script, style"):
                        nav.decompose()
                    text = content_elem.get_text(separator="\n", strip=True)
                    if text and len(text) > 100:
                        description_parts.append(text[:3000])
                        break

            # Look for specific sections
            section_keywords = {
                "What is": "overview",
                "Who can apply": "eligibility",
                "Funding": "funding",
                "Budget": "budget",
                "How to apply": "process",
                "Deadline": "deadline",
                "Timeline": "timeline",
            }

            for heading in soup.select("h2, h3, h4"):
                heading_text = heading.get_text(strip=True)
                for keyword, section_type in section_keywords.items():
                    if keyword.lower() in heading_text.lower():
                        # Get the following content
                        next_elem = heading.find_next_sibling()
                        if next_elem:
                            section_text = next_elem.get_text(strip=True)
                            if section_text and len(section_text) > 20:
                                description_parts.append(f"\n\n**{heading_text}:**\n{section_text[:500]}")
                        break

            description = "\n".join(description_parts)[:5000] if description_parts else f"EU funding opportunity: {title}"

            # Budget/funding amount
            budget = None
            budget_patterns = [
                r"EUR?\s*([\d.,]+)\s*million",
                r"€\s*([\d.,]+)\s*million",
                r"up to EUR?\s*([\d.,]+)",
                r"up to €\s*([\d.,]+)",
                r"([\d.,]+)\s*million EUR",
                r"grant[s]?\s+(?:of\s+)?(?:up to\s+)?EUR?\s*([\d.,]+)",
            ]

            page_text = soup.get_text()
            for pattern in budget_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    try:
                        amount_str = match.group(1).replace(",", ".")
                        amount = float(amount_str)
                        # Check if it's in millions
                        if "million" in pattern.lower() or amount < 100:
                            amount *= 1000000
                        budget = amount
                        break
                    except ValueError:
                        continue

            # Deadlines
            deadline = None
            deadline_patterns = [
                r"deadline[s]?[:\s]+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})",
                r"closes?[:\s]+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})",
                r"(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})",
                r"(\d{4}-\d{2}-\d{2})",
            ]

            for pattern in deadline_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    deadline = match.group(1)
                    break

            # Tags based on content
            tags = ["eu-funding", "horizon-europe", "europe", "research"]

            tag_keywords = {
                "eic": ["eic", "innovation-council"],
                "accelerator": ["startup", "scale-up", "sme"],
                "pathfinder": ["research", "breakthrough", "deep-tech"],
                "transition": ["transition", "commercialization"],
                "digital": ["digital", "technology"],
                "green": ["green-deal", "sustainability", "climate"],
                "health": ["health", "medical"],
                "ai": ["ai", "artificial-intelligence"],
                "msca": ["msca", "fellowship", "researcher"],
                "erc": ["erc", "frontier-research"],
            }

            page_lower = page_text.lower()
            for keyword, tag_list in tag_keywords.items():
                if keyword in page_lower:
                    tags.extend(tag_list)

            # Remove duplicates while preserving order
            tags = list(dict.fromkeys(tags))

            # Themes
            themes = ["research", "innovation", "eu-funding"]
            if "startup" in tags or "sme" in tags:
                themes.append("entrepreneurship")
            if "digital" in tags:
                themes.append("digital-transformation")
            if "green-deal" in tags:
                themes.append("sustainability")

            return RawOpportunity(
                source=self.source_name,
                external_id=f"eu-{topic_id}",
                title=title,
                url=url,
                description=description,
                submission_deadline=deadline,
                end_date=deadline,
                location="European Union",
                is_online=True,
                regions=["EU", "Europe"],
                total_prize_amount=budget,
                prize_currency="EUR",
                tags=tags,
                themes=themes,
                host_name="European Commission",
                host_url="https://ec.europa.eu",
            )

        except Exception as e:
            logger.warning(f"Failed to parse EU Horizon detail page: {e}")
            return None

    async def health_check(self) -> bool:
        """Check if EU Portal is accessible."""
        try:
            client = await self.get_client()
            response = await client.get("https://ec.europa.eu/info/funding-tenders")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"EU Horizon health check failed: {e}")
            return False


def create_eu_horizon_scraper(**kwargs) -> EUHorizonScraper:
    """Create an EU Horizon scraper instance."""
    return EUHorizonScraper(**kwargs)
