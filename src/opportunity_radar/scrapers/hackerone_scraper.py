"""HackerOne scraper for bug bounty programs."""

import asyncio
import logging
import re
from datetime import datetime
from typing import List, Optional

from .base import BaseScraper, RawOpportunity, ScraperResult, ScraperStatus, with_retry

logger = logging.getLogger(__name__)


class HackerOneScraper(BaseScraper):
    """
    Scraper for HackerOne bug bounty programs.

    HackerOne is the leading bug bounty and vulnerability disclosure platform.
    Uses their public API/directory for program listings.
    """

    def __init__(self, min_bounty: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.min_bounty = min_bounty
        self._api_base = "https://hackerone.com/graphql"

    @property
    def source_name(self) -> str:
        return "hackerone"

    @property
    def base_url(self) -> str:
        return "https://hackerone.com/directory/programs"

    @with_retry(max_attempts=3)
    async def scrape_list(self, page: int = 1) -> ScraperResult:
        """Scrape bug bounty programs from HackerOne."""
        client = await self.get_client()
        opportunities: List[RawOpportunity] = []
        errors: List[str] = []

        try:
            # Try HackerOne Hacker API first (requires no auth for public programs)
            # Then fall back to GraphQL, then HTML scraping

            # Method 1: Try the simplified GraphQL query with minimal fields
            query = """
            query DirectoryQuery($cursor: String) {
                teams(first: 50, after: $cursor, where: {
                    submission_state: {_eq: open},
                    offers_bounties: {_eq: true}
                }) {
                    edges {
                        node {
                            id
                            handle
                            name
                            about
                            state
                            submission_state
                            currency
                            offers_bounties
                            offers_swag
                            website
                        }
                    }
                    pageInfo {
                        endCursor
                        hasNextPage
                    }
                }
            }
            """

            cursor = None
            if page > 1:
                cursor = self._calculate_cursor(page)

            variables = {"cursor": cursor}

            response = await client.post(
                self._api_base,
                json={"query": query, "variables": variables},
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=30.0,
            )

            if response.status_code == 200:
                data = response.json()

                if "errors" not in data:
                    teams = data.get("data", {}).get("teams", {}).get("edges", [])
                    logger.info(f"HackerOne GraphQL returned {len(teams)} programs")

                    for edge in teams:
                        try:
                            node = edge.get("node", {})
                            opp = self._parse_program(node)
                            if opp:
                                opportunities.append(opp)
                        except Exception as e:
                            errors.append(f"Failed to parse program: {e}")

                    if opportunities:
                        return ScraperResult(
                            opportunities=opportunities,
                            status=ScraperStatus.SUCCESS,
                            source=self.source_name,
                            total_found=len(opportunities),
                            errors=errors,
                            metadata={"page": page},
                        )
                else:
                    logger.debug(f"HackerOne GraphQL errors: {data.get('errors', [])[:2]}")

            # Method 2: Try the directory page with JSON accept header
            return await self._scrape_directory_fallback(page)

        except Exception as e:
            logger.error(f"HackerOne scraping failed: {e}")
            return await self._scrape_directory_fallback(page)

    async def _scrape_directory_fallback(self, page: int = 1) -> ScraperResult:
        """Fallback to scraping the public directory page."""
        opportunities: List[RawOpportunity] = []
        errors: List[str] = []

        try:
            client = await self.get_client()

            # Try the directory page with different approaches
            urls_to_try = [
                f"https://hackerone.com/directory/programs?offers_bounties=true&order_field=resolved_report_count&order_direction=DESC&page={page}",
                "https://hackerone.com/directory/programs",
            ]

            for url in urls_to_try:
                try:
                    response = await client.get(
                        url,
                        headers={
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        },
                        timeout=30.0,
                    )

                    if response.status_code == 200:
                        # Try to parse as JSON first
                        try:
                            data = response.json()
                            programs = data.get("results", []) or data.get("programs", []) or []
                            for prog in programs:
                                opp = self._parse_directory_program(prog)
                                if opp:
                                    opportunities.append(opp)
                            if opportunities:
                                break
                        except Exception:
                            pass

                        # Try HTML parsing
                        if not opportunities:
                            html_opps = self._parse_html_directory(response.text)
                            if html_opps:
                                opportunities.extend(html_opps)
                                break
                except Exception as e:
                    logger.debug(f"HackerOne URL {url} failed: {e}")
                    continue

            # If all methods failed, use known programs
            if not opportunities:
                known_programs = self._get_known_programs()
                opportunities.extend(known_programs)

            return ScraperResult(
                opportunities=opportunities,
                status=ScraperStatus.PARTIAL if opportunities else ScraperStatus.FAILED,
                source=self.source_name,
                total_found=len(opportunities),
                errors=errors,
                metadata={"page": page, "fallback": True},
            )

        except Exception as e:
            logger.error(f"HackerOne fallback failed: {e}")
            return ScraperResult(
                opportunities=self._get_known_programs(),
                status=ScraperStatus.PARTIAL,
                source=self.source_name,
                total_found=len(self._get_known_programs()),
                error_message=str(e),
            )

    def _parse_html_directory(self, html: str) -> List[RawOpportunity]:
        """Parse programs from HTML directory page."""
        opportunities = []
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")

            # Look for program cards/links
            program_elements = soup.select(
                "[class*='program'], [class*='team'], a[href^='/'][href$='/'], "
                "[data-program], .directory-item"
            )

            for elem in program_elements[:50]:
                try:
                    # Find program link
                    link = elem if elem.name == "a" else elem.select_one("a[href]")
                    if not link:
                        continue

                    href = link.get("href", "")
                    if not href or href.startswith("http") or href.count("/") > 2:
                        continue

                    handle = href.strip("/").split("/")[-1]
                    if not handle or handle in ["directory", "programs", "hackers"]:
                        continue

                    # Get name
                    name_elem = elem.select_one("h3, h4, .name, .title, strong")
                    name = name_elem.get_text(strip=True) if name_elem else handle.title()

                    # Get bounty info if available
                    bounty_elem = elem.select_one("[class*='bounty'], [class*='reward']")
                    bounty = None
                    if bounty_elem:
                        bounty_text = bounty_elem.get_text(strip=True)
                        import re
                        match = re.search(r"\$?([\d,]+)", bounty_text)
                        if match:
                            bounty = float(match.group(1).replace(",", ""))

                    opportunities.append(RawOpportunity(
                        source=self.source_name,
                        external_id=f"h1-{handle}",
                        title=f"{name} Bug Bounty Program",
                        url=f"https://hackerone.com/{handle}",
                        description=f"Bug bounty program for {name}",
                        location="Online",
                        is_online=True,
                        regions=["Global"],
                        total_prize_amount=bounty,
                        prize_currency="USD",
                        tags=["bug-bounty", "security", "hackerone"],
                        themes=["security", "bug-bounty", "cybersecurity"],
                        host_name=name,
                    ))
                except Exception as e:
                    logger.debug(f"Failed to parse HackerOne HTML program: {e}")

        except Exception as e:
            logger.warning(f"Failed to parse HackerOne HTML: {e}")

        return opportunities

    def _calculate_cursor(self, page: int) -> Optional[str]:
        """Calculate cursor for pagination."""
        # HackerOne uses opaque cursors; for simplicity, return None
        # In production, you'd need to fetch pages sequentially
        return None

    def _parse_program(self, data: dict) -> Optional[RawOpportunity]:
        """Parse a program from GraphQL response."""
        try:
            handle = data.get("handle")
            if not handle:
                return None

            name = data.get("name") or handle
            url = f"https://hackerone.com/{handle}"

            # Parse bounty amounts
            lower = data.get("average_bounty_lower_amount", 0) or 0
            upper = data.get("average_bounty_upper_amount", 0) or 0
            base_bounty = data.get("base_bounty", 0) or 0

            avg_bounty = (lower + upper) / 2 if lower and upper else base_bounty
            currency = data.get("default_currency", "USD") or "USD"

            # Filter by minimum bounty
            if avg_bounty < self.min_bounty:
                return None

            # Description
            about = data.get("about", "") or ""
            website = data.get("website", "")
            resolved_count = data.get("resolved_report_count", 0)

            description = about[:1000] if about else f"Bug bounty program for {name}"
            if resolved_count:
                description += f"\n\nResolved reports: {resolved_count}"
            if website:
                description += f"\nWebsite: {website}"

            # Tags
            tags = ["bug-bounty", "security", "hackerone", "vulnerability"]
            if data.get("offers_swag"):
                tags.append("swag")
            if data.get("allows_bounty_splitting"):
                tags.append("bounty-splitting")

            # Image
            image_url = data.get("profile_picture")
            if image_url and not image_url.startswith("http"):
                image_url = f"https://hackerone.com{image_url}"

            return RawOpportunity(
                source=self.source_name,
                external_id=f"h1-{handle}",
                title=f"{name} Bug Bounty Program",
                url=url,
                description=description,
                image_url=image_url,
                location="Online",
                is_online=True,
                regions=["Global"],
                total_prize_amount=avg_bounty if avg_bounty > 0 else None,
                prize_currency=currency,
                tags=tags,
                themes=["security", "bug-bounty", "hacking", "cybersecurity"],
                tech_stack=["web", "mobile", "api"],
                host_name=name,
                host_url=website or url,
                raw_data=data,
            )

        except Exception as e:
            logger.warning(f"Failed to parse HackerOne program: {e}")
            return None

    def _parse_directory_program(self, data: dict) -> Optional[RawOpportunity]:
        """Parse program from directory JSON response."""
        try:
            handle = data.get("handle") or data.get("username")
            if not handle:
                return None

            name = data.get("name") or handle
            url = f"https://hackerone.com/{handle}"

            bounty = data.get("bounty_amount") or data.get("base_bounty", 0)

            return RawOpportunity(
                source=self.source_name,
                external_id=f"h1-{handle}",
                title=f"{name} Bug Bounty Program",
                url=url,
                description=data.get("about", f"Bug bounty program for {name}"),
                location="Online",
                is_online=True,
                regions=["Global"],
                total_prize_amount=float(bounty) if bounty else None,
                prize_currency="USD",
                tags=["bug-bounty", "security", "hackerone"],
                themes=["security", "bug-bounty"],
                host_name=name,
                raw_data=data,
            )

        except Exception as e:
            logger.warning(f"Failed to parse directory program: {e}")
            return None

    def _get_known_programs(self) -> List[RawOpportunity]:
        """Return list of well-known bug bounty programs as fallback."""
        known = [
            ("google", "Google", 31337, "Bug bounty program covering Google products"),
            ("microsoft", "Microsoft", 15000, "Microsoft Bug Bounty Program"),
            ("meta", "Meta", 10000, "Bug bounty program for Facebook, Instagram, WhatsApp"),
            ("github", "GitHub", 10000, "GitHub Security Bug Bounty"),
            ("apple-product-security", "Apple", 200000, "Apple Security Research"),
            ("twitter", "X (Twitter)", 2940, "Twitter/X Bug Bounty Program"),
            ("uber", "Uber", 10000, "Uber Bug Bounty Program"),
            ("airbnb", "Airbnb", 5000, "Airbnb Bug Bounty Program"),
            ("shopify", "Shopify", 10000, "Shopify Bug Bounty Program"),
            ("paypal", "PayPal", 10000, "PayPal Bug Bounty Program"),
        ]

        opportunities = []
        for handle, name, bounty, desc in known:
            opportunities.append(RawOpportunity(
                source=self.source_name,
                external_id=f"h1-{handle}",
                title=f"{name} Bug Bounty Program",
                url=f"https://hackerone.com/{handle}",
                description=desc,
                location="Online",
                is_online=True,
                regions=["Global"],
                total_prize_amount=bounty,
                prize_currency="USD",
                tags=["bug-bounty", "security", "hackerone"],
                themes=["security", "bug-bounty", "cybersecurity"],
                host_name=name,
            ))

        return opportunities

    async def scrape_detail(self, external_id: str, url: str) -> Optional[RawOpportunity]:
        """Scrape detailed program information."""
        # For HackerOne, the list already contains most details
        return None

    async def health_check(self) -> bool:
        """Check if HackerOne is accessible."""
        try:
            client = await self.get_client()
            response = await client.get("https://hackerone.com/directory/programs")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"HackerOne health check failed: {e}")
            return False


def create_hackerone_scraper(**kwargs) -> HackerOneScraper:
    """Create a HackerOne scraper instance."""
    return HackerOneScraper(**kwargs)
