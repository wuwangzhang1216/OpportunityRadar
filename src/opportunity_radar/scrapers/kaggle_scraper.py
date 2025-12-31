"""Kaggle competitions scraper for ML/AI challenges."""

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


class KaggleScraper(BaseScraper):
    """
    Scraper for Kaggle competitions (ML/AI).

    Kaggle is the largest platform for machine learning competitions.
    Uses Playwright for JavaScript-rendered content.
    """

    # Competition categories
    CATEGORIES = {
        "featured": "Featured",
        "research": "Research",
        "getting-started": "Getting Started",
        "playground": "Playground",
        "community": "Community",
    }

    def __init__(self, category: str = "all", headless: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.category = category
        self.headless = headless
        self._browser: Optional["Browser"] = None
        self._playwright = None

    @property
    def source_name(self) -> str:
        return "kaggle"

    @property
    def base_url(self) -> str:
        return "https://www.kaggle.com/competitions"

    async def _get_browser(self) -> "Browser":
        """Get or create Playwright browser instance using Firefox for better anti-detection."""
        if self._browser is None or not self._browser.is_connected():
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
            # Use Firefox - better for avoiding bot detection
            self._browser = await self._playwright.firefox.launch(
                headless=self.headless,
            )
            logger.info("Kaggle: Playwright Firefox browser launched")

        return self._browser

    async def _create_page(self) -> "Page":
        """Create a new browser page."""
        browser = await self._get_browser()
        # Simple context - Firefox doesn't need Chrome-specific headers
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            locale="en-US",
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
        """Check if Kaggle is accessible."""
        try:
            client = await self.get_client()
            response = await client.get("https://www.kaggle.com/competitions")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Kaggle health check failed: {e}")
            return False

    @with_retry(max_attempts=3)
    async def scrape_list(self, page: int = 1) -> ScraperResult:
        """Scrape Kaggle competitions list using Playwright."""
        opportunities: List[RawOpportunity] = []
        errors: List[str] = []
        browser_page = None

        try:
            browser_page = await self._create_page()

            logger.info(f"Navigating to Kaggle competitions...")
            # Use domcontentloaded instead of networkidle for faster loading
            await browser_page.goto(self.base_url, wait_until="domcontentloaded", timeout=60000)

            # Wait for competition content to load (retry a few times)
            max_wait_attempts = 3
            for attempt in range(max_wait_attempts):
                await browser_page.wait_for_timeout(3000)

                # Check if competitions are loaded
                links = await browser_page.query_selector_all("a[href*='/competitions/']")
                if len(links) > 5:  # We expect more than just nav links
                    logger.debug(f"Found {len(links)} competition links after {attempt + 1} attempts")
                    break

                if attempt < max_wait_attempts - 1:
                    logger.debug(f"Attempt {attempt + 1}: Only {len(links)} links, waiting more...")
                    # Scroll to trigger lazy loading
                    await browser_page.evaluate("window.scrollBy(0, 500)")

            # Final scroll to load more competitions
            await self._scroll_page(browser_page)
            await browser_page.wait_for_timeout(2000)

            html_content = await browser_page.content()
            logger.debug(f"Page HTML length: {len(html_content)}")
            soup = BeautifulSoup(html_content, "lxml")

            # Find competition cards
            competition_cards = self._find_competition_cards(soup)
            logger.info(f"Found {len(competition_cards)} Kaggle competitions")

            for card in competition_cards:
                try:
                    opp = self._parse_competition_card(card)
                    if opp:
                        opportunities.append(opp)
                except Exception as e:
                    errors.append(f"Failed to parse competition: {e}")
                    logger.warning(f"Failed to parse Kaggle competition: {e}")

            return ScraperResult(
                opportunities=opportunities,
                status=ScraperStatus.SUCCESS if opportunities else ScraperStatus.PARTIAL,
                source=self.source_name,
                total_found=len(opportunities),
                errors=errors,
                metadata={"page": page, "category": self.category},
            )

        except Exception as e:
            logger.error(f"Kaggle scraping failed: {e}")
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
                    for (let i = 0; i < 5; i++) {
                        window.scrollBy(0, window.innerHeight);
                        await delay(800);
                    }
                    window.scrollTo(0, 0);
                }
            """)
        except Exception:
            pass

    def _find_competition_cards(self, soup: BeautifulSoup) -> list:
        """Find competition cards in the page."""
        # Find all competition links and extract unique competitions
        all_links = soup.select("a[href*='/competitions/']")
        seen_urls = set()
        unique_cards = []

        for link in all_links:
            href = link.get("href", "")
            # Skip navigation and invalid links
            if not href or href in ["/competitions", "/competitions/"]:
                continue
            if "?" in href or "#" in href:
                continue
            # Must be a specific competition link
            parts = href.rstrip("/").split("/")
            if len(parts) < 2 or parts[-1] == "competitions":
                continue

            if href not in seen_urls:
                seen_urls.add(href)
                # Get a reasonable parent container (5 levels up max)
                parent = link
                for _ in range(5):
                    if parent.parent and parent.parent.name in ["div", "li", "article"]:
                        parent = parent.parent
                    else:
                        break
                unique_cards.append((href, parent))

        logger.debug(f"Found {len(unique_cards)} unique competition links")
        return unique_cards

    def _parse_competition_card(self, card_tuple) -> Optional[RawOpportunity]:
        """Parse a Kaggle competition card."""
        try:
            # Unpack tuple (href, parent_element)
            if isinstance(card_tuple, tuple):
                href, card = card_tuple
            else:
                card = card_tuple
                href = None

            # Get URL and link element
            link_elem = None
            if not href:
                link_elem = card if card.name == "a" else card.select_one("a[href*='/competitions/']")
                if not link_elem:
                    return None
                href = link_elem.get("href", "")
            else:
                # Find the link element for this href
                link_elem = card if card.name == "a" else card.select_one(f"a[href='{href}']")
                if not link_elem:
                    link_elem = card.select_one("a[href*='/competitions/']")

            if not href:
                return None

            url = href
            if not url.startswith("http"):
                url = f"https://www.kaggle.com{url}"

            # Extract competition ID
            external_id = url.rstrip("/").split("/")[-1]
            if not external_id or external_id == "competitions":
                return None

            # Title extraction - get full link text and parse it
            title = None
            description = None

            if link_elem:
                full_text = link_elem.get_text(strip=True)
                # Kaggle format: "{Title}more_vert{Description}{Category}..."
                # Split on "more_vert" which is the menu icon text
                if "more_vert" in full_text:
                    parts = full_text.split("more_vert", 1)
                    title = parts[0].strip()
                    if len(parts) > 1:
                        # Description is before the category (Getting Started, Featured, etc.)
                        rest = parts[1].strip()
                        # Remove trailing category labels
                        categories = ["Getting Started", "Featured", "Research", "Playground", "Community"]
                        for cat in categories:
                            if rest.endswith(cat):
                                rest = rest[:-len(cat)].strip()
                        description = rest if rest else None
                elif full_text:
                    # No more_vert, try to extract title from the beginning
                    title = full_text[:100].strip()

            # Fallback: Use ID formatted nicely
            if not title:
                title = external_id.replace("-", " ").title()

            # Clean title
            title = re.sub(r"\s+", " ", title).strip()
            if len(title) > 200:
                title = title[:197] + "..."

            # Description/subtitle (if not already extracted from link text)
            if not description:
                desc_elem = card.select_one("[class*='subtitle'], [class*='description'], p")
                if desc_elem:
                    description = desc_elem.get_text(strip=True)

            # Prize
            prize_elem = card.select_one("[class*='prize'], [class*='reward']")
            total_prize = None
            prize_currency = "USD"
            if prize_elem:
                prize_text = prize_elem.get_text(strip=True)
                total_prize = self._parse_prize(prize_text)
                if "knowledge" in prize_text.lower() or "kudos" in prize_text.lower():
                    total_prize = 0  # Knowledge/Kudos competitions

            # Deadline
            deadline_elem = card.select_one("[class*='deadline'], [class*='end'], time")
            deadline = None
            if deadline_elem:
                deadline = deadline_elem.get_text(strip=True)
                # Or check datetime attribute
                deadline = deadline_elem.get("datetime") or deadline

            # Teams/participants count
            teams_elem = card.select_one("[class*='teams'], [class*='participants']")
            participants = None
            if teams_elem:
                match = re.search(r"([\d,]+)", teams_elem.get_text())
                if match:
                    participants = int(match.group(1).replace(",", ""))

            # Competition type/category
            type_elem = card.select_one("[class*='category'], [class*='type'], [class*='tag']")
            comp_type = type_elem.get_text(strip=True) if type_elem else "competition"

            # Image
            img = card.select_one("img")
            image_url = None
            if img:
                image_url = img.get("src") or img.get("data-src")
                if image_url and image_url.startswith("//"):
                    image_url = "https:" + image_url

            # Tags based on title/description
            tags = ["kaggle", "ml", "ai", "data-science", "machine-learning"]
            text = (title + " " + (description or "")).lower()
            if "nlp" in text or "text" in text or "language" in text:
                tags.append("nlp")
            if "vision" in text or "image" in text or "computer vision" in text:
                tags.append("computer-vision")
            if "tabular" in text:
                tags.append("tabular")
            if "time series" in text:
                tags.append("time-series")

            return RawOpportunity(
                source=self.source_name,
                external_id=f"kaggle-{external_id}",
                title=title,
                url=url,
                description=description or f"Kaggle Competition: {title}",
                image_url=image_url,
                submission_deadline=deadline,
                end_date=deadline,
                location="Online",
                is_online=True,
                regions=["Global"],
                total_prize_amount=total_prize,
                prize_currency=prize_currency,
                tags=tags,
                themes=["machine-learning", "data-science"],
                tech_stack=["python", "tensorflow", "pytorch", "scikit-learn"],
                host_name="Kaggle",
                host_url="https://www.kaggle.com",
                raw_data={"type": comp_type, "participants": participants},
            )

        except Exception as e:
            logger.warning(f"Failed to parse Kaggle competition: {e}")
            return None

    def _parse_prize(self, prize_text: str) -> Optional[float]:
        """Parse prize amount from text."""
        if not prize_text:
            return None

        # Handle special cases
        lower = prize_text.lower()
        if any(x in lower for x in ["knowledge", "kudos", "swag", "medals"]):
            return 0

        # Match patterns like "$100,000", "100K", "$1M"
        match = re.search(r"[\$€£]?\s*([\d,]+)\s*([kKmM])?", prize_text)
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
        """Scrape detailed competition information."""
        try:
            client = await self.get_client()
            response = await client.get(url)

            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, "lxml")

            # Title
            title_elem = soup.select_one("h1, [class*='title']")
            title = title_elem.get_text(strip=True) if title_elem else external_id

            # Description
            desc_elem = soup.select_one("[class*='description'], [class*='overview'], #description")
            description = None
            if desc_elem:
                description = desc_elem.get_text(strip=True)[:3000]

            # Prize
            prize_elem = soup.select_one("[class*='prize']")
            total_prize = self._parse_prize(prize_elem.get_text()) if prize_elem else None

            # Timeline
            timeline_elem = soup.select_one("[class*='timeline'], [class*='deadline']")
            deadline = timeline_elem.get_text(strip=True) if timeline_elem else None

            # Evaluation metric
            eval_elem = soup.select_one("[class*='evaluation'], [class*='metric']")
            evaluation = eval_elem.get_text(strip=True) if eval_elem else None

            # Data description
            data_elem = soup.select_one("[class*='data'], #data")
            data_desc = data_elem.get_text(strip=True)[:1000] if data_elem else None

            full_desc = description
            if evaluation:
                full_desc = f"{full_desc}\n\nEvaluation: {evaluation}"
            if data_desc:
                full_desc = f"{full_desc}\n\nData: {data_desc}"

            return RawOpportunity(
                source=self.source_name,
                external_id=external_id,
                title=title,
                url=url,
                description=full_desc,
                submission_deadline=deadline,
                end_date=deadline,
                location="Online",
                is_online=True,
                regions=["Global"],
                total_prize_amount=total_prize,
                tags=["kaggle", "ml", "ai", "data-science"],
                host_name="Kaggle",
                host_url="https://www.kaggle.com",
                raw_data={},
            )

        except Exception as e:
            logger.error(f"Failed to scrape Kaggle detail: {e}")
            return None


def create_kaggle_scraper(**kwargs) -> KaggleScraper:
    """Create a Kaggle scraper instance."""
    return KaggleScraper(**kwargs)
