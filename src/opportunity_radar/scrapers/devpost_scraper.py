"""Devpost hackathon scraper."""

import asyncio
import logging
import re
from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin, urlencode

from bs4 import BeautifulSoup

from .base import BaseScraper, RawOpportunity, ScraperResult, ScraperStatus, with_retry

logger = logging.getLogger(__name__)


class DevpostScraper(BaseScraper):
    """Scraper for Devpost hackathons."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._api_base = "https://devpost.com/api/hackathons"

    @property
    def source_name(self) -> str:
        return "devpost"

    @property
    def base_url(self) -> str:
        return "https://devpost.com/hackathons"

    @with_retry(max_attempts=3)
    async def scrape_list(self, page: int = 1) -> ScraperResult:
        """Scrape hackathon list from Devpost API."""
        client = await self.get_client()
        opportunities: List[RawOpportunity] = []
        errors: List[str] = []

        try:
            # Scrape both open and upcoming hackathons
            all_hackathons = []
            for status in ["open", "upcoming"]:
                params = {
                    "page": page,
                    "status": status,
                    "order_by": "recently-added",
                    "per_page": 24,
                }
                url = f"{self._api_base}?{urlencode(params)}"
                response = await client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    all_hackathons.extend(data.get("hackathons", []))

                await asyncio.sleep(0.5)  # Small delay between requests

            # Deduplicate by ID
            seen_ids = set()
            hackathons = []
            for h in all_hackathons:
                hid = h.get("id") or h.get("url", "").rstrip("/").split("/")[-1]
                if hid and hid not in seen_ids:
                    seen_ids.add(hid)
                    hackathons.append(h)

            for hackathon in hackathons:
                try:
                    opp = self._parse_api_hackathon(hackathon)
                    if opp:
                        opportunities.append(opp)
                except Exception as e:
                    errors.append(f"Failed to parse hackathon: {e}")
                    logger.warning(f"Failed to parse hackathon: {e}")

            return ScraperResult(
                opportunities=opportunities,
                status=ScraperStatus.SUCCESS if not errors else ScraperStatus.PARTIAL,
                source=self.source_name,
                total_found=len(opportunities),
                errors=errors,
                metadata={"page": page, "statuses": ["open", "upcoming"]},
            )

        except Exception as e:
            logger.error(f"Devpost list scraping failed: {e}")
            return ScraperResult(
                opportunities=[],
                status=ScraperStatus.FAILED,
                source=self.source_name,
                error_message=str(e),
            )

    async def _scrape_list_html(self, page: int = 1) -> ScraperResult:
        """Fallback HTML scraping for hackathon list."""
        client = await self.get_client()
        opportunities: List[RawOpportunity] = []
        errors: List[str] = []

        try:
            url = f"{self.base_url}?page={page}"
            response = await client.get(url)

            if response.status_code != 200:
                return ScraperResult(
                    opportunities=[],
                    status=ScraperStatus.FAILED,
                    source=self.source_name,
                    error_message=f"HTTP {response.status_code}",
                )

            soup = BeautifulSoup(response.text, "lxml")

            # Find hackathon tiles
            tiles = soup.select(".hackathon-tile, .challenge-listing")

            for tile in tiles:
                try:
                    opp = self._parse_html_tile(tile)
                    if opp:
                        opportunities.append(opp)
                except Exception as e:
                    errors.append(f"Failed to parse tile: {e}")

            return ScraperResult(
                opportunities=opportunities,
                status=ScraperStatus.SUCCESS if opportunities else ScraperStatus.PARTIAL,
                source=self.source_name,
                total_found=len(opportunities),
                errors=errors,
                metadata={"page": page, "method": "html"},
            )

        except Exception as e:
            return ScraperResult(
                opportunities=[],
                status=ScraperStatus.FAILED,
                source=self.source_name,
                error_message=str(e),
            )

    def _parse_api_hackathon(self, data: dict) -> Optional[RawOpportunity]:
        """Parse hackathon from Devpost API response."""
        try:
            # Handle case where data might be a string (URL) instead of dict
            if isinstance(data, str):
                logger.warning(f"Received string instead of dict: {data[:100]}")
                return None

            if not isinstance(data, dict):
                logger.warning(f"Unexpected data type: {type(data)}")
                return None

            # Extract ID from URL or use numeric ID
            url = data.get("url", "")
            external_id = data.get("id")
            if not external_id and url:
                # Extract subdomain from URL like "https://gemini3.devpost.com/"
                if "devpost.com" in url:
                    external_id = url.replace("https://", "").replace("http://", "").split(".devpost.com")[0]

            if not external_id:
                return None

            # Parse prizes - handle HTML format like "$<span data-currency-value>100,000</span>"
            prizes = []
            prize_amount_str = data.get("prize_amount", "")
            if prize_amount_str:
                # Remove HTML tags and extract number
                clean_amount = re.sub(r"<[^>]+>", "", str(prize_amount_str))
                amount_match = re.search(r"[\$€£]?\s*([\d,]+)", clean_amount)
                if amount_match:
                    amount = float(amount_match.group(1).replace(",", ""))
                    prizes.append({
                        "type": "total",
                        "name": "Total Prizes",
                        "amount": amount,
                        "currency": "USD",
                    })

            # Parse themes/tags
            themes_raw = data.get("themes", [])
            themes = []
            if isinstance(themes_raw, list):
                for t in themes_raw:
                    if isinstance(t, dict):
                        themes.append(t.get("name", ""))
                    elif isinstance(t, str):
                        themes.append(t)
            themes = [t for t in themes if t]  # Remove empty strings

            # Parse tech platforms
            platforms = data.get("platforms", [])
            tech_stack = []
            if isinstance(platforms, list):
                for p in platforms:
                    if isinstance(p, dict):
                        tech_stack.append(p.get("name", ""))
                    elif isinstance(p, str):
                        tech_stack.append(p)
            tech_stack = [t for t in tech_stack if t]

            # Determine if online
            location_data = data.get("displayed_location", {})
            if isinstance(location_data, dict):
                location_str = location_data.get("location", "Online")
            else:
                location_str = str(location_data) if location_data else "Online"
            is_online = "online" in location_str.lower() or "virtual" in location_str.lower()

            # Parse date range from string like "Dec 17, 2025 - Feb 09, 2026"
            submission_dates = data.get("submission_period_dates", "")
            start_date = None
            end_date = None
            if isinstance(submission_dates, str) and " - " in submission_dates:
                parts = submission_dates.split(" - ")
                if len(parts) == 2:
                    start_date = parts[0].strip()
                    end_date = parts[1].strip()
            elif isinstance(submission_dates, dict):
                start_date = submission_dates.get("starts_at")
                end_date = submission_dates.get("ends_at")

            # Build image URL (handle protocol-relative URLs)
            image_url = data.get("thumbnail_url") or data.get("cover_image_url")
            if image_url and image_url.startswith("//"):
                image_url = "https:" + image_url

            return RawOpportunity(
                source=self.source_name,
                external_id=str(external_id),
                title=data.get("title", "Untitled Hackathon"),
                url=url,
                description=data.get("tagline", "") or data.get("time_left_to_submission", ""),
                image_url=image_url,
                start_date=start_date,
                end_date=end_date,
                submission_deadline=end_date,
                location=location_str,
                is_online=is_online,
                regions=["Global"] if is_online else [location_str],
                prizes=prizes,
                total_prize_amount=prizes[0]["amount"] if prizes else None,
                tags=themes[:10],
                themes=themes[:10],
                tech_stack=tech_stack[:10],
                host_name=data.get("organization_name"),
                raw_data=data,
            )

        except Exception as e:
            logger.warning(f"Failed to parse API hackathon: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _parse_html_tile(self, tile) -> Optional[RawOpportunity]:
        """Parse hackathon from HTML tile element."""
        try:
            # Find link and title
            link = tile.select_one("a.link-to-hackathon, a[data-hackathon-slug]")
            if not link:
                link = tile.select_one("a")

            if not link:
                return None

            url = link.get("href", "")
            if not url.startswith("http"):
                url = urljoin(self.base_url, url)

            external_id = url.rstrip("/").split("/")[-1]

            title_elem = tile.select_one(".title, h3, h2")
            title = title_elem.get_text(strip=True) if title_elem else "Untitled"

            # Description/tagline
            desc_elem = tile.select_one(".tagline, .description, p")
            description = desc_elem.get_text(strip=True) if desc_elem else None

            # Image
            img = tile.select_one("img")
            image_url = img.get("src") if img else None

            # Prize
            prize_elem = tile.select_one(".prize, .prize-amount")
            prize_text = prize_elem.get_text(strip=True) if prize_elem else None
            total_prize = self._parse_prize_text(prize_text)

            # Dates
            date_elem = tile.select_one(".date, .dates, time")
            date_text = date_elem.get_text(strip=True) if date_elem else None
            start_date, end_date = self._parse_date_range(date_text)

            # Location
            loc_elem = tile.select_one(".location, .host-location")
            location = loc_elem.get_text(strip=True) if loc_elem else "Online"
            is_online = "online" in location.lower() or "virtual" in location.lower()

            # Tags
            tag_elems = tile.select(".tag, .theme, .challenge-tag")
            tags = [t.get_text(strip=True) for t in tag_elems]

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
                regions=["Global"] if is_online else [location],
                total_prize_amount=total_prize,
                tags=tags[:10],
                raw_data={},
            )

        except Exception as e:
            logger.warning(f"Failed to parse HTML tile: {e}")
            return None

    @with_retry(max_attempts=3)
    async def scrape_detail(self, external_id: str, url: str) -> Optional[RawOpportunity]:
        """Scrape detailed information for a single hackathon."""
        client = await self.get_client()

        try:
            response = await client.get(url)
            if response.status_code != 200:
                logger.warning(f"Detail page returned {response.status_code} for {url}")
                return None

            soup = BeautifulSoup(response.text, "lxml")

            # Title - try multiple selectors, prefer og:title for accuracy
            title = "Untitled"
            og_title = soup.select_one('meta[property="og:title"]')
            if og_title and og_title.get("content"):
                title = og_title.get("content")
            else:
                # Find h1 with actual text content
                for h1 in soup.select("h1"):
                    text = h1.get_text(strip=True)
                    if text and len(text) > 3:
                        title = text
                        break

            # Description - from challenge description section
            description = None
            desc_elem = soup.select_one("#challenge-description, .challenge-description")
            if desc_elem:
                description = desc_elem.get_text(separator=" ", strip=True)[:5000]

            # Full rules/requirements text
            rules_text = ""
            rules_elem = soup.select_one("#rules, .rules")
            if rules_elem:
                rules_text = rules_elem.get_text(strip=True)

            # Eligibility section
            eligibility = []
            elig_elem = soup.select_one("#eligibility, .eligibility")
            if elig_elem:
                rules_text += " " + elig_elem.get_text(strip=True)
                for li in elig_elem.select("li"):
                    eligibility.append({
                        "type": "text",
                        "rule": li.get_text(strip=True),
                    })

            # Extract team size from rules
            team_min, team_max = self._extract_team_size(rules_text)

            # Prizes - look for prize items
            prizes = []
            total_prize = None
            prize_items = soup.select(".prize, article .prize")
            for item in prize_items:
                prize_title = item.select_one(".prize-title, h3, h4")
                prize_desc = item.select_one(".prize-description, p")
                if prize_title:
                    name = prize_title.get_text(strip=True)
                    desc = prize_desc.get_text(strip=True) if prize_desc else ""
                    amount = self._parse_prize_text(name + " " + desc)
                    prizes.append({
                        "type": "prize",
                        "name": name,
                        "description": desc,
                        "amount": amount,
                        "currency": "USD",
                    })
                    if amount:
                        total_prize = (total_prize or 0) + amount

            # Themes/Tags from sidebar or theme elements
            themes = []
            theme_elems = soup.select('[class*="theme"]:not([class*="themes-link"])')
            for t in theme_elems:
                text = t.get_text(strip=True)
                # Filter out dates and empty strings
                if text and len(text) < 50 and not any(month in text for month in ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]):
                    themes.append(text)
            themes = list(dict.fromkeys(themes))  # Remove duplicates while preserving order

            # Tech stack from software section or description
            tech_stack = []
            sw_elem = soup.select_one(".software, .technologies")
            if sw_elem:
                tech_items = sw_elem.select("span, li, a")
                tech_stack = [t.get_text(strip=True) for t in tech_items if t.get_text(strip=True)]

            # If no tech found, try to extract from description
            if not tech_stack and description:
                common_tech = ["Python", "JavaScript", "React", "Node.js", "TensorFlow", "PyTorch",
                              "AWS", "GCP", "Azure", "Docker", "Kubernetes", "HTML", "CSS",
                              "TypeScript", "Vue", "Angular", "Flutter", "Swift", "Kotlin"]
                tech_stack = [t for t in common_tech if t.lower() in description.lower()]

            # Dates from timeline or submission period
            start_date = None
            end_date = None
            date_section = soup.select_one(".submission-period, .timeline-container, [class*='date']")
            if date_section:
                dates_text = date_section.get_text()
                start_date, end_date = self._parse_date_range(dates_text)

            # Check for student only
            full_text = (rules_text + " " + (description or "")).lower()
            student_only = "student" in full_text and any(
                word in full_text for word in ["only", "must be", "required", "eligible"]
            )

            # Image - og:image is most reliable
            image_url = None
            og_image = soup.select_one('meta[property="og:image"]')
            if og_image and og_image.get("content"):
                image_url = og_image.get("content")
            else:
                img = soup.select_one(".challenge-logo img, .cover-image img, header img")
                if img:
                    image_url = img.get("src")

            # Host/organizer
            host_name = None
            host_elem = soup.select_one(".host-info, .organizer, .managed-by a")
            if host_elem:
                host_name = host_elem.get_text(strip=True)

            # Location info
            location = "Online"
            is_online = True
            loc_elem = soup.select_one(".location, [class*='location']")
            if loc_elem:
                loc_text = loc_elem.get_text(strip=True)
                if loc_text and "online" not in loc_text.lower():
                    location = loc_text
                    is_online = "online" in loc_text.lower() or "virtual" in loc_text.lower()

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
                team_min=team_min,
                team_max=team_max,
                prizes=prizes,
                total_prize_amount=total_prize,
                tags=themes[:10],
                themes=themes[:10],
                tech_stack=tech_stack[:10],
                host_name=host_name,
                eligibility_rules=eligibility,
                student_only=student_only,
                raw_data={},
            )

        except Exception as e:
            logger.error(f"Failed to scrape detail for {external_id}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _extract_team_size(self, text: str) -> tuple[Optional[int], Optional[int]]:
        """Extract team size requirements from text."""
        if not text:
            return None, None

        text = text.lower()

        # Look for patterns like "teams of 2-5" or "1-4 members"
        range_match = re.search(r"(\d+)\s*[-–to]+\s*(\d+)\s*(?:members?|people|participants?)?", text)
        if range_match:
            return int(range_match.group(1)), int(range_match.group(2))

        # Look for "up to X" pattern
        up_to_match = re.search(r"up\s*to\s*(\d+)", text)
        if up_to_match:
            return 1, int(up_to_match.group(1))

        # Look for "at least X" pattern
        at_least_match = re.search(r"at\s*least\s*(\d+)", text)
        if at_least_match:
            return int(at_least_match.group(1)), None

        # Solo allowed
        if "solo" in text or "individual" in text:
            return 1, 1

        return None, None

    def _parse_prize_text(self, text: Optional[str]) -> Optional[float]:
        """Parse prize amount from text."""
        if not text:
            return None

        # Match currency symbols and amounts
        match = re.search(r"[\$€£]?\s*([\d,]+(?:\.\d{2})?)\s*(?:k|K)?", text)
        if match:
            amount_str = match.group(1).replace(",", "")
            if not amount_str:  # Empty string check
                return None
            try:
                amount = float(amount_str)
                # Handle "k" suffix (thousands)
                if "k" in text.lower():
                    amount *= 1000
                return amount
            except ValueError:
                return None

        return None

    def _parse_date_range(self, text: Optional[str]) -> tuple[Optional[str], Optional[str]]:
        """Parse date range from text."""
        if not text:
            return None, None

        # Common patterns
        # "Jan 15 - Jan 20, 2024"
        # "January 15, 2024 - January 20, 2024"
        # "15-20 January 2024"

        # Try to find date patterns
        date_pattern = r"(\w+\s+\d{1,2}(?:,?\s*\d{4})?)"
        matches = re.findall(date_pattern, text)

        if len(matches) >= 2:
            return matches[0], matches[-1]
        elif len(matches) == 1:
            return matches[0], matches[0]

        return None, None


# Factory function
def create_devpost_scraper(**kwargs) -> DevpostScraper:
    """Create a Devpost scraper instance."""
    return DevpostScraper(**kwargs)
