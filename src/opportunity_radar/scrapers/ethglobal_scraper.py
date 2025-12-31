"""ETHGlobal hackathon scraper for Web3/Blockchain events."""

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


class ETHGlobalScraper(BaseScraper):
    """
    Scraper for ETHGlobal hackathons (Web3/Blockchain).

    ETHGlobal hosts high-value hackathons with prize pools often exceeding $100k.
    Uses Playwright for JavaScript-rendered content.
    """

    def __init__(self, headless: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.headless = headless
        self._browser: Optional["Browser"] = None
        self._playwright = None

    @property
    def source_name(self) -> str:
        return "ethglobal"

    @property
    def base_url(self) -> str:
        return "https://ethglobal.com/events"

    async def _get_browser(self) -> "Browser":
        """Get or create Playwright browser instance."""
        if self._browser is None or not self._browser.is_connected():
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
            )
            logger.info("ETHGlobal: Playwright browser launched")

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

    async def health_check(self) -> bool:
        """Check if ETHGlobal is accessible."""
        try:
            client = await self.get_client()
            response = await client.get(self.base_url)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"ETHGlobal health check failed: {e}")
            return False

    @with_retry(max_attempts=3)
    async def scrape_list(self, page: int = 1) -> ScraperResult:
        """Scrape ETHGlobal events page."""
        # ETHGlobal shows all events on one page
        if page > 1:
            return ScraperResult(
                opportunities=[],
                status=ScraperStatus.SUCCESS,
                source=self.source_name,
                total_found=0,
            )

        opportunities: List[RawOpportunity] = []
        errors: List[str] = []
        browser_page = None

        try:
            browser_page = await self._create_page()

            logger.info("Navigating to ETHGlobal events...")
            await browser_page.goto(self.base_url, wait_until="networkidle", timeout=60000)
            await browser_page.wait_for_timeout(3000)

            html_content = await browser_page.content()
            soup = BeautifulSoup(html_content, "lxml")

            # Find event cards - ETHGlobal uses various layouts
            event_cards = self._find_event_cards(soup)
            logger.info(f"Found {len(event_cards)} ETHGlobal events")

            for card in event_cards:
                try:
                    opp = self._parse_event_card(card)
                    if opp:
                        opportunities.append(opp)
                except Exception as e:
                    errors.append(f"Failed to parse event: {e}")
                    logger.warning(f"Failed to parse ETHGlobal event: {e}")

            return ScraperResult(
                opportunities=opportunities,
                status=ScraperStatus.SUCCESS if opportunities else ScraperStatus.PARTIAL,
                source=self.source_name,
                total_found=len(opportunities),
                errors=errors,
                metadata={"method": "playwright"},
            )

        except Exception as e:
            logger.error(f"ETHGlobal scraping failed: {e}")
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

    def _find_event_cards(self, soup: BeautifulSoup) -> list:
        """Find event cards using multiple selectors."""
        selectors = [
            "a[href*='/events/']",
            "[class*='event-card']",
            "[class*='EventCard']",
            "div[class*='event']",
        ]

        for selector in selectors:
            cards = soup.select(selector)
            # Filter to actual event links
            filtered = [c for c in cards if self._is_valid_event_card(c)]
            if filtered:
                return filtered

        return []

    def _is_valid_event_card(self, element) -> bool:
        """Check if element is a valid event card."""
        href = element.get("href", "")
        if "/events/" in href and href.count("/") >= 2:
            # Exclude navigation links
            if any(x in href for x in ["/events/past", "/events/upcoming", "/events#"]):
                return False
            return True

        # Check for nested link
        link = element.select_one("a[href*='/events/']")
        if link:
            href = link.get("href", "")
            return "/events/" in href and not any(x in href for x in ["past", "upcoming", "#"])

        return False

    def _parse_event_card(self, card) -> Optional[RawOpportunity]:
        """Parse an ETHGlobal event card."""
        try:
            # Get URL
            url = card.get("href", "")
            if not url:
                link = card.select_one("a[href*='/events/']")
                url = link.get("href", "") if link else ""

            if not url:
                return None

            if not url.startswith("http"):
                url = f"https://ethglobal.com{url}"

            # Extract event ID from URL
            external_id = url.rstrip("/").split("/")[-1]
            if not external_id or external_id in ["events", ""]:
                return None

            # Title
            title_elem = card.select_one("h2, h3, h4, [class*='title'], [class*='name']")
            title = title_elem.get_text(strip=True) if title_elem else external_id.replace("-", " ").title()

            # Clean title
            title = re.sub(r"\s+", " ", title).strip()

            # Image
            img = card.select_one("img")
            image_url = None
            if img:
                image_url = img.get("src") or img.get("data-src")
                if image_url and not image_url.startswith("http"):
                    image_url = f"https://ethglobal.com{image_url}"

            # Location/Type
            location_elem = card.select_one("[class*='location'], [class*='city'], [class*='type']")
            location = location_elem.get_text(strip=True) if location_elem else "TBD"

            card_text = card.get_text().lower()
            is_online = any(word in card_text for word in ["online", "virtual", "remote"])

            # Date
            date_elem = card.select_one("[class*='date'], time, [datetime]")
            date_text = date_elem.get_text(strip=True) if date_elem else None
            start_date, end_date = self._parse_date(date_text)

            # Prize info (if visible)
            prize_elem = card.select_one("[class*='prize'], [class*='bounty']")
            total_prize = None
            if prize_elem:
                prize_text = prize_elem.get_text(strip=True)
                total_prize = self._parse_prize(prize_text)

            # Default tags for ETHGlobal
            tags = ["web3", "blockchain", "ethereum", "ethglobal"]

            return RawOpportunity(
                source=self.source_name,
                external_id=f"ethglobal-{external_id}",
                title=title,
                url=url,
                description=f"ETHGlobal Hackathon: {title}",
                image_url=image_url,
                start_date=start_date,
                end_date=end_date,
                submission_deadline=end_date,
                location=location,
                is_online=is_online,
                regions=["Global"] if is_online else [location],
                total_prize_amount=total_prize,
                tags=tags,
                themes=["web3", "defi", "nft", "dao"],
                tech_stack=["solidity", "ethereum", "web3.js"],
                host_name="ETHGlobal",
                host_url="https://ethglobal.com",
                raw_data={},
            )

        except Exception as e:
            logger.warning(f"Failed to parse ETHGlobal event: {e}")
            return None

    def _parse_date(self, date_text: Optional[str]) -> tuple[Optional[str], Optional[str]]:
        """Parse date from text."""
        if not date_text:
            return None, None

        # Clean up
        date_text = re.sub(r"\s+", " ", date_text.strip())

        # Try to find date patterns
        if " - " in date_text or " to " in date_text.lower():
            parts = re.split(r"\s*[-–]\s*|\s+to\s+", date_text, flags=re.IGNORECASE)
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()

        return date_text, date_text

    def _parse_prize(self, prize_text: str) -> Optional[float]:
        """Parse prize amount from text."""
        if not prize_text:
            return None

        # Match patterns like "$100k", "$100,000", "100K USD"
        match = re.search(r"[\$]?\s*([\d,]+)\s*([kKmM])?", prize_text)
        if match:
            amount = float(match.group(1).replace(",", ""))
            multiplier = match.group(2)
            if multiplier and multiplier.lower() == "k":
                amount *= 1000
            elif multiplier and multiplier.lower() == "m":
                amount *= 1000000
            return amount

        return None

    async def scrape_detail(self, external_id: str, url: str) -> Optional[RawOpportunity]:
        """Scrape detailed event information."""
        browser_page = None
        try:
            browser_page = await self._create_page()
            await browser_page.goto(url, wait_until="networkidle", timeout=30000)
            await browser_page.wait_for_timeout(2000)

            html = await browser_page.content()
            soup = BeautifulSoup(html, "lxml")

            # Title
            title_elem = soup.select_one("h1, [class*='title']")
            title = title_elem.get_text(strip=True) if title_elem else external_id

            # Description
            desc_elem = soup.select_one("[class*='description'], [class*='about'], main p")
            description = desc_elem.get_text(strip=True)[:2000] if desc_elem else None

            # Prize pool
            prize_elem = soup.select_one("[class*='prize'], [class*='bounty']")
            total_prize = None
            if prize_elem:
                total_prize = self._parse_prize(prize_elem.get_text())

            # Dates
            date_section = soup.select_one("[class*='date'], [class*='schedule']")
            start_date, end_date = None, None
            if date_section:
                start_date, end_date = self._parse_date(date_section.get_text())

            # Location
            loc_elem = soup.select_one("[class*='location'], [class*='venue']")
            location = loc_elem.get_text(strip=True) if loc_elem else "TBD"
            is_online = "online" in location.lower() or "virtual" in location.lower()

            return RawOpportunity(
                source=self.source_name,
                external_id=external_id,
                title=title,
                url=url,
                description=description,
                start_date=start_date,
                end_date=end_date,
                submission_deadline=end_date,
                location=location,
                is_online=is_online,
                total_prize_amount=total_prize,
                tags=["web3", "blockchain", "ethereum", "ethglobal"],
                host_name="ETHGlobal",
                host_url="https://ethglobal.com",
                raw_data={},
            )

        except Exception as e:
            logger.error(f"Failed to scrape ETHGlobal detail: {e}")
            return None
        finally:
            if browser_page:
                try:
                    await browser_page.context.close()
                except Exception:
                    pass


def create_ethglobal_scraper(**kwargs) -> ETHGlobalScraper:
    """Create an ETHGlobal scraper instance."""
    return ETHGlobalScraper(**kwargs)
