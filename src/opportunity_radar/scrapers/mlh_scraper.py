"""MLH (Major League Hacking) hackathon scraper with Playwright browser automation."""

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


class MLHScraper(BaseScraper):
    """
    Scraper for MLH hackathons using Playwright browser automation.

    MLH uses Cloudflare protection which blocks simple HTTP requests.
    This scraper uses a real browser to bypass the protection.
    """

    # MLH season URLs
    SEASONS = {
        "2025": "https://mlh.io/seasons/2025/events",
        "2024": "https://mlh.io/seasons/2024/events",
    }

    def __init__(self, season: str = "2025", headless: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.season = season
        self.headless = headless
        self._browser: Optional["Browser"] = None
        self._playwright = None

    @property
    def source_name(self) -> str:
        return "mlh"

    @property
    def base_url(self) -> str:
        return self.SEASONS.get(self.season, self.SEASONS["2025"])

    async def _get_browser(self) -> "Browser":
        """Get or create Playwright browser instance."""
        if self._browser is None or not self._browser.is_connected():
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()

            # Use Firefox for better anti-detection
            self._browser = await self._playwright.firefox.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                ]
            )
            logger.info("Playwright browser launched")

        return self._browser

    async def _create_stealth_page(self) -> "Page":
        """Create a new page with stealth settings."""
        browser = await self._get_browser()

        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) "
                "Gecko/20100101 Firefox/121.0"
            ),
            locale="en-US",
            timezone_id="America/New_York",
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            }
        )

        page = await context.new_page()

        # Add stealth scripts to avoid detection
        await page.add_init_script("""
            // Override navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Override plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });

            // Override platform
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32'
            });
        """)

        return page

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
        """Check if MLH is accessible via browser."""
        try:
            page = await self._create_stealth_page()
            try:
                response = await page.goto(
                    self.base_url,
                    wait_until="domcontentloaded",
                    timeout=30000
                )

                # Wait a bit for any JS to load
                await page.wait_for_timeout(2000)

                # Check if we got blocked
                content = await page.content()
                if "Access denied" in content or "blocked" in content.lower():
                    logger.warning("MLH access denied - may be blocked")
                    return False

                return response is not None and response.status < 400

            finally:
                await page.context.close()

        except Exception as e:
            logger.error(f"MLH health check failed: {e}")
            return False

    @with_retry(max_attempts=3)
    async def scrape_list(self, page: int = 1) -> ScraperResult:
        """
        Scrape hackathon list from MLH using Playwright.
        MLH doesn't have pagination - all events are on one page per season.
        """
        # Only process page 1 since MLH has no pagination
        if page > 1:
            return ScraperResult(
                opportunities=[],
                status=ScraperStatus.SUCCESS,
                source=self.source_name,
                total_found=0,
                metadata={"page": page, "season": self.season},
            )

        opportunities: List[RawOpportunity] = []
        errors: List[str] = []
        browser_page = None

        try:
            browser_page = await self._create_stealth_page()

            logger.info(f"Navigating to MLH {self.season} events page...")

            # Navigate with extended timeout
            response = await browser_page.goto(
                self.base_url,
                wait_until="networkidle",
                timeout=60000
            )

            if response is None or response.status >= 400:
                return ScraperResult(
                    opportunities=[],
                    status=ScraperStatus.FAILED,
                    source=self.source_name,
                    error_message=f"HTTP {response.status if response else 'No response'}",
                )

            # Wait for content to load
            await browser_page.wait_for_timeout(3000)

            # Wait for event cards to appear
            try:
                await browser_page.wait_for_selector(
                    ".event, .event-wrapper, [class*='event']",
                    timeout=10000
                )
            except Exception:
                logger.warning("Event cards selector timeout - page may have different structure")

            # Get page content
            html_content = await browser_page.content()

            # Check for block/challenge page
            if self._is_blocked(html_content):
                logger.error("Blocked by Cloudflare or similar protection")
                return ScraperResult(
                    opportunities=[],
                    status=ScraperStatus.FAILED,
                    source=self.source_name,
                    error_message="Blocked by anti-bot protection",
                )

            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, "lxml")

            # Try multiple selectors for event cards
            event_cards = self._find_event_cards(soup)

            logger.info(f"Found {len(event_cards)} MLH events for season {self.season}")

            for card in event_cards:
                try:
                    opp = self._parse_event_card(card)
                    if opp:
                        opportunities.append(opp)
                except Exception as e:
                    errors.append(f"Failed to parse event card: {e}")
                    logger.warning(f"Failed to parse MLH event card: {e}")

            return ScraperResult(
                opportunities=opportunities,
                status=ScraperStatus.SUCCESS if opportunities else ScraperStatus.PARTIAL,
                source=self.source_name,
                total_found=len(opportunities),
                errors=errors,
                metadata={"page": 1, "season": self.season, "method": "playwright"},
            )

        except Exception as e:
            logger.error(f"MLH scraping failed: {e}")
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

    def _is_blocked(self, html: str) -> bool:
        """Check if the response is a block/challenge page."""
        block_indicators = [
            "Access denied",
            "Just a moment",
            "Checking your browser",
            "Enable JavaScript and cookies",
            "cf-browser-verification",
            "challenge-platform",
        ]
        return any(indicator in html for indicator in block_indicators)

    def _find_event_cards(self, soup: BeautifulSoup) -> list:
        """Find event cards using multiple selector strategies."""
        selectors = [
            ".event",
            ".event-wrapper",
            "[class*='event-card']",
            "div[data-event-id]",
            "article.hackathon",
            ".row .event",
            "div.event.feature",
            # MLH specific selectors
            ".event-card",
            ".hackathon-card",
            "a[href*='/events/']",
        ]

        for selector in selectors:
            cards = soup.select(selector)
            if cards:
                logger.debug(f"Found {len(cards)} cards with selector: {selector}")
                return cards

        # Fallback: look for any container with event-like structure
        # (has image, title, date, location)
        potential_cards = []
        for div in soup.find_all("div"):
            has_image = div.find("img") is not None
            has_link = div.find("a") is not None
            text = div.get_text()
            has_date = bool(re.search(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b", text))

            if has_image and has_link and has_date and len(text) < 1000:
                potential_cards.append(div)

        if potential_cards:
            logger.debug(f"Found {len(potential_cards)} potential cards via heuristic")
            return potential_cards[:50]  # Limit to prevent false positives

        return []

    def _parse_event_card(self, card) -> Optional[RawOpportunity]:
        """Parse a single MLH event card."""
        try:
            # Find the event link
            link = card.select_one("a[href*='mlh.io'], a.event-link, a[href*='/events/']")
            if not link:
                link = card.select_one("a[href]")

            if not link:
                # Card itself might be the link
                if card.name == "a" and card.get("href"):
                    link = card
                else:
                    return None

            url = link.get("href", "")
            if not url:
                return None

            # Make absolute URL
            if not url.startswith("http"):
                if url.startswith("/"):
                    url = f"https://mlh.io{url}"
                else:
                    url = f"https://mlh.io/{url}"

            # Extract external ID from URL or data attribute
            external_id = card.get("data-event-id") or card.get("id")
            if not external_id:
                # Try to extract from URL
                url_parts = url.rstrip("/").split("/")
                external_id = url_parts[-1] if url_parts else None

                if not external_id or external_id in ["events", ""]:
                    # Generate from title
                    title_elem = card.select_one(".event-name, .name, h3, h4, h5, strong")
                    if title_elem:
                        external_id = re.sub(r"[^\w]+", "-", title_elem.get_text(strip=True).lower())[:50]

            if not external_id:
                return None

            # Title - try multiple selectors
            title_elem = card.select_one(
                ".event-name, .name, h3, h4, h5, .title, strong, "
                "[class*='name'], [class*='title']"
            )
            title = title_elem.get_text(strip=True) if title_elem else "Untitled MLH Hackathon"

            # Clean up title
            title = re.sub(r"\s+", " ", title).strip()
            if len(title) > 200:
                title = title[:197] + "..."

            # Image/logo
            img = card.select_one("img.logo, img.event-logo, img[class*='logo'], img")
            image_url = None
            if img:
                image_url = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
                if image_url:
                    if image_url.startswith("//"):
                        image_url = "https:" + image_url
                    elif not image_url.startswith("http"):
                        image_url = f"https://mlh.io{image_url}"

            # Location
            location_elem = card.select_one(
                ".event-location, .location, .city, "
                "[class*='location'], [class*='city']"
            )
            location = location_elem.get_text(strip=True) if location_elem else "TBD"
            location = re.sub(r"\s+", " ", location).strip()

            # Determine if online/hybrid
            is_online = False
            location_lower = location.lower() if location else ""
            card_text = card.get_text().lower()

            if any(word in location_lower or word in card_text
                   for word in ["digital", "online", "virtual", "hybrid", "remote"]):
                is_online = True

            # Dates
            date_elem = card.select_one(
                ".event-date, .date, time, "
                "[class*='date'], [datetime]"
            )
            date_text = date_elem.get_text(strip=True) if date_elem else None

            # Try to find date in card text if not found
            if not date_text:
                date_match = re.search(
                    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}",
                    card.get_text(),
                    re.IGNORECASE
                )
                if date_match:
                    date_text = date_match.group(0)

            start_date, end_date = self._parse_mlh_date(date_text)

            # Mode (in-person, digital, hybrid)
            mode_elem = card.select_one(
                ".event-hybrid-notes, .mode, .format, "
                "[class*='hybrid'], [class*='mode']"
            )
            mode = mode_elem.get_text(strip=True) if mode_elem else None
            if mode:
                mode_lower = mode.lower()
                if "digital" in mode_lower or "online" in mode_lower:
                    is_online = True
                    if "tbd" in location.lower():
                        location = "Online"

            # Tags/themes
            tags = ["mlh", f"mlh-{self.season}"]
            theme_elems = card.select(".theme, .track, .tag, [class*='tag']")
            for theme in theme_elems[:5]:
                tag_text = theme.get_text(strip=True).lower()
                if tag_text and tag_text not in tags:
                    tags.append(tag_text)

            # MLH member hackathon badge
            is_member = card.select_one(".member-badge, .mlh-member, [class*='member']") is not None
            if is_member:
                tags.append("mlh-member")

            return RawOpportunity(
                source=self.source_name,
                external_id=f"mlh-{self.season}-{external_id}",
                title=title,
                url=url,
                description=f"MLH {self.season} Season Hackathon: {title}",
                image_url=image_url,
                start_date=start_date,
                end_date=end_date,
                submission_deadline=end_date,
                location=location,
                is_online=is_online,
                regions=["Global"] if is_online else [self._extract_region(location)],
                team_min=1,
                team_max=4,  # MLH standard team size
                tags=tags,
                themes=tags,
                host_name="Major League Hacking",
                host_url="https://mlh.io",
                raw_data={
                    "season": self.season,
                    "mode": mode,
                    "is_member": is_member,
                },
            )

        except Exception as e:
            logger.warning(f"Failed to parse MLH event card: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _parse_mlh_date(self, date_text: Optional[str]) -> tuple[Optional[str], Optional[str]]:
        """Parse MLH date format (e.g., 'Jan 12th - 14th, 2024')."""
        if not date_text:
            return None, None

        try:
            # Clean up the text
            date_text = date_text.strip()

            # MLH formats:
            # "Jan 12th - 14th, 2024"
            # "January 12 - 14, 2024"
            # "Jan 12 - Jan 14, 2024"
            # "TBD"

            if "tbd" in date_text.lower():
                return None, None

            # Remove ordinal suffixes
            date_text = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", date_text)

            # Try to split by " - " or " – " or " to "
            parts = re.split(r"\s*[-–]\s*|\s+to\s+", date_text)

            if len(parts) == 2:
                start_part = parts[0].strip()
                end_part = parts[1].strip()

                # If end part doesn't have month, add it from start
                if not re.search(r"[A-Za-z]", end_part.split(",")[0]):
                    # Extract month from start
                    month_match = re.match(r"([A-Za-z]+)", start_part)
                    if month_match:
                        end_part = f"{month_match.group(1)} {end_part}"

                return start_part, end_part

            return date_text, date_text

        except Exception as e:
            logger.debug(f"Failed to parse MLH date '{date_text}': {e}")
            return None, None

    def _extract_region(self, location: str) -> str:
        """Extract region/country from location string."""
        if not location:
            return "Unknown"

        location_lower = location.lower()

        # Common region mappings
        REGIONS = {
            "usa": "United States",
            "us": "United States",
            "united states": "United States",
            "america": "United States",
            "uk": "United Kingdom",
            "united kingdom": "United Kingdom",
            "england": "United Kingdom",
            "canada": "Canada",
            "india": "India",
            "germany": "Germany",
            "france": "France",
            "australia": "Australia",
            "singapore": "Singapore",
            "japan": "Japan",
            "china": "China",
            "brazil": "Brazil",
            "mexico": "Mexico",
            "spain": "Spain",
            "italy": "Italy",
            "netherlands": "Netherlands",
            "sweden": "Sweden",
            "poland": "Poland",
        }

        for key, region in REGIONS.items():
            if key in location_lower:
                return region

        # Return as-is if no mapping found
        return location.split(",")[-1].strip() if "," in location else location

    @with_retry(max_attempts=3)
    async def scrape_detail(self, external_id: str, url: str) -> Optional[RawOpportunity]:
        """Scrape detailed information for a single MLH hackathon."""
        browser_page = None

        try:
            browser_page = await self._create_stealth_page()

            response = await browser_page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000
            )

            if response is None or response.status >= 400:
                return None

            await browser_page.wait_for_timeout(2000)

            html_content = await browser_page.content()
            soup = BeautifulSoup(html_content, "lxml")

            # Title
            title_elem = soup.select_one("h1, .event-title, .hackathon-name")
            title = title_elem.get_text(strip=True) if title_elem else "Untitled"

            # Description
            desc_elem = soup.select_one(".event-description, .description, .about, main p")
            description = desc_elem.get_text(strip=True)[:3000] if desc_elem else None

            # Image
            img = soup.select_one("meta[property='og:image'], .event-logo img, .logo img")
            image_url = None
            if img:
                image_url = img.get("content") or img.get("src")
                if image_url and image_url.startswith("//"):
                    image_url = "https:" + image_url

            # Date/time details
            date_section = soup.select_one(".event-dates, .dates, .when, [class*='date']")
            start_date = None
            end_date = None
            if date_section:
                date_text = date_section.get_text(strip=True)
                start_date, end_date = self._parse_mlh_date(date_text)

            # Location
            loc_section = soup.select_one(".event-location, .location, .where, [class*='location']")
            location = loc_section.get_text(strip=True) if loc_section else "TBD"
            is_online = "online" in location.lower() or "virtual" in location.lower()

            # Prizes (if listed)
            prizes = []
            prize_section = soup.select_one(".prizes, .rewards, [class*='prize']")
            if prize_section:
                prize_items = prize_section.select("li, .prize-item")
                for item in prize_items[:10]:
                    prizes.append({
                        "type": "prize",
                        "name": item.get_text(strip=True)[:200],
                        "amount": None,
                        "currency": "USD",
                    })

            # Rules/requirements
            rules_section = soup.select_one(".rules, .requirements, .eligibility")
            student_only = False
            if rules_section:
                rules_text = rules_section.get_text(strip=True).lower()
                student_only = "student" in rules_text

            # Sponsors
            sponsors = []
            sponsor_section = soup.select_one(".sponsors, .partners, [class*='sponsor']")
            if sponsor_section:
                sponsor_imgs = sponsor_section.select("img")
                for img in sponsor_imgs[:20]:
                    alt = img.get("alt", "")
                    if alt:
                        sponsors.append(alt)

            return RawOpportunity(
                source=self.source_name,
                external_id=external_id,
                title=title,
                url=url,
                description=description,
                image_url=image_url,
                start_date=start_date,
                end_date=end_date,
                submission_deadline=end_date,
                location=location,
                is_online=is_online,
                regions=["Global"] if is_online else [self._extract_region(location)],
                team_min=1,
                team_max=4,
                prizes=prizes,
                tags=["mlh", f"mlh-{self.season}"],
                themes=[],
                host_name="Major League Hacking",
                host_url="https://mlh.io",
                student_only=student_only,
                raw_data={"season": self.season, "sponsors": sponsors},
            )

        except Exception as e:
            logger.error(f"Failed to scrape MLH detail for {external_id}: {e}")
            return None

        finally:
            if browser_page:
                try:
                    await browser_page.context.close()
                except Exception:
                    pass

    async def scrape_all_seasons(self, seasons: Optional[List[str]] = None) -> ScraperResult:
        """Scrape hackathons from multiple MLH seasons."""
        seasons = seasons or list(self.SEASONS.keys())
        all_opportunities: List[RawOpportunity] = []
        all_errors: List[str] = []

        for season in seasons:
            self.season = season
            logger.info(f"Scraping MLH season {season}...")

            result = await self.scrape_list(page=1)

            if result.success:
                all_opportunities.extend(result.opportunities)
                logger.info(f"Found {len(result.opportunities)} events in season {season}")
            else:
                all_errors.append(f"Season {season}: {result.error_message}")

            await asyncio.sleep(self.request_delay)

        status = ScraperStatus.SUCCESS
        if all_errors:
            status = ScraperStatus.PARTIAL if all_opportunities else ScraperStatus.FAILED

        return ScraperResult(
            opportunities=all_opportunities,
            status=status,
            source=self.source_name,
            total_found=len(all_opportunities),
            errors=all_errors,
            error_message="; ".join(all_errors) if all_errors else None,
            metadata={"seasons": seasons},
        )


# Factory function
def create_mlh_scraper(season: str = "2025", headless: bool = True, **kwargs) -> MLHScraper:
    """Create an MLH scraper instance."""
    return MLHScraper(season=season, headless=headless, **kwargs)
