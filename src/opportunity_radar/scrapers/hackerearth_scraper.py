"""HackerEarth challenges and hackathons scraper."""

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


class HackerEarthScraper(BaseScraper):
    """
    Scraper for HackerEarth challenges and hackathons.

    HackerEarth hosts enterprise-sponsored hackathons, often with
    job opportunities and significant prize pools.
    """

    # Challenge types
    CHALLENGE_TYPES = {
        "hackathon": "/challenges/hackathon/",
        "hiring": "/challenges/hiring/",
        "competitive": "/challenges/competitive/",
    }

    def __init__(
        self,
        challenge_type: str = "hackathon",
        headless: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.challenge_type = challenge_type
        self.headless = headless
        self._browser: Optional["Browser"] = None
        self._playwright = None

    @property
    def source_name(self) -> str:
        return "hackerearth"

    @property
    def base_url(self) -> str:
        return f"https://www.hackerearth.com/challenges/hackathon/"

    async def _get_browser(self) -> "Browser":
        """Get or create Playwright browser instance."""
        if self._browser is None or not self._browser.is_connected():
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
            )
            logger.info("HackerEarth: Playwright browser launched")

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
        """Check if HackerEarth is accessible."""
        try:
            client = await self.get_client()
            response = await client.get(self.base_url, follow_redirects=True)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"HackerEarth health check failed: {e}")
            return False

    @with_retry(max_attempts=3)
    async def scrape_list(self, page: int = 1) -> ScraperResult:
        """Scrape HackerEarth challenges list."""
        opportunities: List[RawOpportunity] = []
        errors: List[str] = []
        browser_page = None

        try:
            browser_page = await self._create_page()

            # HackerEarth has different sections: ongoing, upcoming, past
            urls_to_scrape = [
                f"https://www.hackerearth.com/challenges/hackathon/?page={page}",
            ]

            for url in urls_to_scrape:
                logger.info(f"Navigating to HackerEarth: {url}")
                await browser_page.goto(url, wait_until="networkidle", timeout=60000)
                await browser_page.wait_for_timeout(3000)

                # Scroll to load lazy content
                await self._scroll_page(browser_page)

                html_content = await browser_page.content()
                soup = BeautifulSoup(html_content, "lxml")

                # Find challenge cards
                challenge_cards = self._find_challenge_cards(soup)
                logger.info(f"Found {len(challenge_cards)} HackerEarth challenges")

                for card in challenge_cards:
                    try:
                        opp = self._parse_challenge_card(card)
                        if opp:
                            opportunities.append(opp)
                    except Exception as e:
                        errors.append(f"Failed to parse challenge: {e}")
                        logger.warning(f"Failed to parse HackerEarth challenge: {e}")

            # Deduplicate
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
                metadata={"page": page, "type": self.challenge_type},
            )

        except Exception as e:
            logger.error(f"HackerEarth scraping failed: {e}")
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

    async def _scroll_page(self, page: "Page"):
        """Scroll page to load lazy content."""
        try:
            await page.evaluate("""
                async () => {
                    const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
                    for (let i = 0; i < 3; i++) {
                        window.scrollBy(0, window.innerHeight);
                        await delay(500);
                    }
                    window.scrollTo(0, 0);
                }
            """)
        except Exception:
            pass

    def _find_challenge_cards(self, soup: BeautifulSoup) -> list:
        """Find challenge cards in the page."""
        selectors = [
            ".challenge-card-modern",
            ".challenge-card",
            "[class*='challenge-card']",
            ".event-card",
            "[class*='ChallengeCard']",
            "a[href*='/challenges/']",
        ]

        for selector in selectors:
            cards = soup.select(selector)
            if cards:
                # Filter valid challenge cards
                valid = [c for c in cards if self._is_valid_challenge(c)]
                if valid:
                    return valid

        # Fallback: find all challenge links and get their containers
        links = soup.select("a[href*='/challenges/hackathon/']")
        seen = set()
        containers = []
        for link in links:
            href = link.get("href", "")
            if href not in seen and "?" not in href:
                seen.add(href)
                parent = link.find_parent("div", class_=re.compile(r"card|challenge|event"))
                containers.append(parent or link)

        return containers[:30]

    def _is_valid_challenge(self, element) -> bool:
        """Check if element is a valid challenge card."""
        # Check for challenge link
        link = element.select_one("a[href*='/challenges/']")
        if link:
            href = link.get("href", "")
            # Filter out category pages
            if any(x in href for x in ["/hackathon/?", "/competitive/?", "/hiring/?"]):
                return False
            return True
        return False

    def _parse_challenge_card(self, card) -> Optional[RawOpportunity]:
        """Parse a HackerEarth challenge card."""
        try:
            # Get URL
            link = card.select_one("a[href*='/challenges/']")
            if not link:
                if card.name == "a":
                    link = card
                else:
                    return None

            url = link.get("href", "")
            if not url:
                return None

            if not url.startswith("http"):
                url = f"https://www.hackerearth.com{url}"

            # Extract challenge ID
            parts = url.rstrip("/").split("/")
            external_id = parts[-1] if parts else None
            if not external_id:
                return None

            # Title
            title_elem = card.select_one(
                ".challenge-name, .event-name, h3, h4, "
                "[class*='title'], [class*='name']"
            )
            title = title_elem.get_text(strip=True) if title_elem else external_id.replace("-", " ").title()

            # Clean title
            title = re.sub(r"\s+", " ", title).strip()

            # Company/Host
            company_elem = card.select_one(
                ".company-name, .organizer, [class*='company'], [class*='host']"
            )
            host_name = company_elem.get_text(strip=True) if company_elem else "HackerEarth"

            # Prize
            prize_elem = card.select_one("[class*='prize'], [class*='reward']")
            total_prize = None
            if prize_elem:
                prize_text = prize_elem.get_text(strip=True)
                total_prize = self._parse_prize(prize_text)

            # Status (ongoing, upcoming, ended)
            status_elem = card.select_one("[class*='status'], [class*='state'], .label")
            status = status_elem.get_text(strip=True).lower() if status_elem else "unknown"

            # Skip ended challenges
            if "ended" in status or "closed" in status:
                return None

            # Dates
            date_elem = card.select_one("[class*='date'], [class*='time'], time")
            start_date, end_date = None, None
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                start_date, end_date = self._parse_date(date_text)

            # Participants
            participants_elem = card.select_one("[class*='participant'], [class*='registered']")
            participants = None
            if participants_elem:
                match = re.search(r"([\d,]+)", participants_elem.get_text())
                if match:
                    participants = int(match.group(1).replace(",", ""))

            # Image
            img = card.select_one("img")
            image_url = None
            if img:
                image_url = img.get("src") or img.get("data-src")
                if image_url and image_url.startswith("//"):
                    image_url = "https:" + image_url
                elif image_url and not image_url.startswith("http"):
                    image_url = f"https://www.hackerearth.com{image_url}"

            # Location (usually online for HackerEarth)
            location_elem = card.select_one("[class*='location']")
            location = location_elem.get_text(strip=True) if location_elem else "Online"
            is_online = "online" in location.lower() or location == "Online"

            # Tags
            tags = ["hackerearth", "hackathon"]
            tag_elems = card.select("[class*='tag'], .skill-tag")
            for tag_elem in tag_elems[:5]:
                tag_text = tag_elem.get_text(strip=True).lower()
                if tag_text and tag_text not in tags:
                    tags.append(tag_text)

            # Add tech tags based on content
            card_text = card.get_text().lower()
            tech_keywords = {
                "python": "python", "javascript": "javascript", "java": "java",
                "machine learning": "ml", "ai": "ai", "data science": "data-science",
                "web": "web", "mobile": "mobile", "blockchain": "blockchain",
                "cloud": "cloud", "aws": "aws", "azure": "azure",
            }
            for keyword, tag in tech_keywords.items():
                if keyword in card_text and tag not in tags:
                    tags.append(tag)

            return RawOpportunity(
                source=self.source_name,
                external_id=f"hackerearth-{external_id}",
                title=title,
                url=url,
                description=f"HackerEarth Hackathon: {title}",
                image_url=image_url,
                start_date=start_date,
                end_date=end_date,
                submission_deadline=end_date,
                location=location,
                is_online=is_online,
                regions=["Global"] if is_online else ["India"],  # Most HE events target India
                total_prize_amount=total_prize,
                tags=tags,
                themes=["innovation", "technology"],
                host_name=host_name,
                host_url="https://www.hackerearth.com",
                raw_data={"status": status, "participants": participants},
            )

        except Exception as e:
            logger.warning(f"Failed to parse HackerEarth challenge: {e}")
            return None

    def _parse_date(self, date_text: Optional[str]) -> tuple[Optional[str], Optional[str]]:
        """Parse date from text."""
        if not date_text:
            return None, None

        # Clean up
        date_text = re.sub(r"\s+", " ", date_text.strip())

        # Try to find date range patterns
        # "Jan 15 - Feb 20, 2024"
        # "15 Jan - 20 Feb 2024"
        if " - " in date_text or " to " in date_text.lower():
            parts = re.split(r"\s*[-–]\s*|\s+to\s+", date_text, flags=re.IGNORECASE)
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()

        # Single date - use as both start and end
        return date_text, date_text

    def _parse_prize(self, prize_text: str) -> Optional[float]:
        """Parse prize amount from text."""
        if not prize_text:
            return None

        # Handle Indian Rupees (common on HackerEarth)
        if "₹" in prize_text or "inr" in prize_text.lower() or "rs" in prize_text.lower():
            # Convert to USD (rough estimate: 1 USD = 83 INR)
            match = re.search(r"([\d,]+)\s*([lakLAKcrCR]+)?", prize_text.replace("₹", "").replace(",", ""))
            if match:
                amount = float(match.group(1))
                suffix = match.group(2)
                if suffix:
                    suffix_lower = suffix.lower()
                    if "lak" in suffix_lower or "lac" in suffix_lower:
                        amount *= 100000  # 1 lakh = 100,000
                    elif "cr" in suffix_lower:
                        amount *= 10000000  # 1 crore = 10,000,000
                return amount / 83  # Convert to USD

        # USD patterns
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
        """Scrape detailed challenge information."""
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
            desc_elem = soup.select_one(
                "[class*='description'], [class*='about'], "
                "[class*='overview'], .challenge-desc"
            )
            description = desc_elem.get_text(strip=True)[:3000] if desc_elem else None

            # Prize details
            prize_section = soup.select_one("[class*='prize'], [class*='reward']")
            total_prize = None
            prizes = []
            if prize_section:
                total_prize = self._parse_prize(prize_section.get_text())
                # Try to find individual prizes
                prize_items = prize_section.select("li, [class*='prize-item']")
                for item in prize_items[:5]:
                    prizes.append({
                        "type": "prize",
                        "name": item.get_text(strip=True)[:100],
                        "amount": self._parse_prize(item.get_text()),
                        "currency": "USD",
                    })

            # Timeline
            timeline_elem = soup.select_one("[class*='timeline'], [class*='schedule']")
            start_date, end_date = None, None
            if timeline_elem:
                start_date, end_date = self._parse_date(timeline_elem.get_text())

            # Eligibility
            eligibility_elem = soup.select_one("[class*='eligibility'], [class*='rules']")
            eligibility = eligibility_elem.get_text(strip=True)[:500] if eligibility_elem else None

            # Host/Company
            host_elem = soup.select_one("[class*='company'], [class*='organizer'], [class*='host']")
            host_name = host_elem.get_text(strip=True) if host_elem else "HackerEarth"

            # Image
            img = soup.select_one("[class*='banner'] img, [class*='cover'] img, .challenge-image img")
            image_url = None
            if img:
                image_url = img.get("src")
                if image_url and not image_url.startswith("http"):
                    image_url = f"https://www.hackerearth.com{image_url}"

            full_desc = description
            if eligibility:
                full_desc = f"{full_desc}\n\nEligibility: {eligibility}"

            return RawOpportunity(
                source=self.source_name,
                external_id=external_id,
                title=title,
                url=url,
                description=full_desc,
                image_url=image_url,
                start_date=start_date,
                end_date=end_date,
                submission_deadline=end_date,
                location="Online",
                is_online=True,
                total_prize_amount=total_prize,
                prizes=prizes,
                tags=["hackerearth", "hackathon"],
                host_name=host_name,
                host_url="https://www.hackerearth.com",
                raw_data={},
            )

        except Exception as e:
            logger.error(f"Failed to scrape HackerEarth detail: {e}")
            return None
        finally:
            if browser_page:
                try:
                    await browser_page.context.close()
                except Exception:
                    pass


def create_hackerearth_scraper(**kwargs) -> HackerEarthScraper:
    """Create a HackerEarth scraper instance."""
    return HackerEarthScraper(**kwargs)
