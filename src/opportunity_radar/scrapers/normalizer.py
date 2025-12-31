"""Data normalizer for converting raw scraped data to database models."""

import logging
import re
from datetime import datetime
from typing import List, Optional, Tuple
from zoneinfo import ZoneInfo

from dateutil import parser as date_parser

from .base import RawOpportunity
from ..schemas.opportunity import OpportunityCreate, BatchSchema, TimelineSchema, PrizeSchema

logger = logging.getLogger(__name__)


class DataNormalizer:
    """Normalize raw scraped data to unified schema."""

    # Common timezone mappings
    TIMEZONE_MAP = {
        "EST": "America/New_York",
        "EDT": "America/New_York",
        "PST": "America/Los_Angeles",
        "PDT": "America/Los_Angeles",
        "CST": "America/Chicago",
        "CDT": "America/Chicago",
        "MST": "America/Denver",
        "MDT": "America/Denver",
        "UTC": "UTC",
        "GMT": "UTC",
    }

    def normalize(
        self, raw: RawOpportunity
    ) -> Tuple[OpportunityCreate, dict, dict, List[dict]]:
        """
        Convert raw data to database-ready schemas.

        Returns:
            Tuple of (opportunity_data, batch_data, timeline_data, prizes_data)
        """
        # Normalize opportunity
        opportunity_data = {
            "external_id": raw.external_id,
            "source": raw.source,
            "category": self._determine_category(raw),
            "title": self._clean_text(raw.title),
            "description": self._clean_text(raw.description) if raw.description else None,
            "tags": self._normalize_tags(raw.tags + raw.themes),
            "industry": self._extract_industries(raw),
            "tech_stack": self._normalize_tech_stack(raw.tech_stack),
            "locale": self._extract_locales(raw),
            "url": raw.url,
            "image_url": raw.image_url,
        }

        # Normalize batch
        batch_data = {
            "year": self._extract_year(raw),
            "season": self._extract_season(raw),
            "remote_ok": raw.is_online,
            "regions": self._normalize_regions(raw.regions, raw.location),
            "team_min": raw.team_min or 1,
            "team_max": raw.team_max,
            "student_only": raw.student_only,
            "startup_stages": [],
            "sponsors": self._extract_sponsors(raw),
            "status": self._determine_status(raw),
        }

        # Normalize timeline
        timeline_data = {
            "registration_opens_at": self._parse_datetime(raw.start_date),
            "registration_closes_at": self._parse_datetime(raw.registration_deadline),
            "event_starts_at": self._parse_datetime(raw.start_date),
            "event_ends_at": self._parse_datetime(raw.end_date),
            "submission_deadline": self._parse_datetime(
                raw.submission_deadline or raw.end_date
            ),
            "timezone": self._extract_timezone(raw),
        }

        # Normalize prizes
        prizes_data = self._normalize_prizes(raw)

        return opportunity_data, batch_data, timeline_data, prizes_data

    def _clean_text(self, text: Optional[str]) -> Optional[str]:
        """Clean and normalize text."""
        if not text:
            return None
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text).strip()
        # Remove HTML tags if any
        text = re.sub(r"<[^>]+>", "", text)
        return text[:5000] if text else None  # Limit length

    def _determine_category(self, raw: RawOpportunity) -> str:
        """Determine opportunity category."""
        title_lower = raw.title.lower()
        desc_lower = (raw.description or "").lower()
        combined = title_lower + " " + desc_lower

        if any(word in combined for word in ["hackathon", "hack", "hacking"]):
            return "hackathon"
        elif any(word in combined for word in ["grant", "funding", "subsidy"]):
            return "grant"
        elif any(word in combined for word in ["accelerator", "incubator"]):
            return "accelerator"
        elif any(word in combined for word in ["pitch", "competition", "challenge"]):
            return "competition"
        return "hackathon"  # Default for Devpost/MLH

    def _normalize_tags(self, tags: List[str]) -> List[str]:
        """Normalize and deduplicate tags."""
        normalized = set()
        for tag in tags:
            if tag:
                # Clean and lowercase
                clean_tag = tag.strip().lower()
                # Remove special characters
                clean_tag = re.sub(r"[^\w\s-]", "", clean_tag)
                if clean_tag and len(clean_tag) > 1:
                    normalized.add(clean_tag)
        return sorted(list(normalized))[:20]  # Limit to 20 tags

    def _normalize_tech_stack(self, tech_stack: List[str]) -> List[str]:
        """Normalize technology stack items."""
        # Common tech name mappings
        TECH_MAP = {
            "javascript": "JavaScript",
            "typescript": "TypeScript",
            "python": "Python",
            "react": "React",
            "reactjs": "React",
            "react.js": "React",
            "nodejs": "Node.js",
            "node.js": "Node.js",
            "node": "Node.js",
            "vue": "Vue.js",
            "vuejs": "Vue.js",
            "angular": "Angular",
            "tensorflow": "TensorFlow",
            "pytorch": "PyTorch",
            "aws": "AWS",
            "gcp": "GCP",
            "azure": "Azure",
            "docker": "Docker",
            "kubernetes": "Kubernetes",
            "k8s": "Kubernetes",
            "mongodb": "MongoDB",
            "postgresql": "PostgreSQL",
            "postgres": "PostgreSQL",
            "mysql": "MySQL",
            "redis": "Redis",
            "graphql": "GraphQL",
            "rest": "REST API",
            "api": "API",
            "machine learning": "Machine Learning",
            "ml": "Machine Learning",
            "ai": "AI",
            "artificial intelligence": "AI",
            "blockchain": "Blockchain",
            "web3": "Web3",
            "solidity": "Solidity",
            "rust": "Rust",
            "go": "Go",
            "golang": "Go",
            "java": "Java",
            "swift": "Swift",
            "kotlin": "Kotlin",
            "flutter": "Flutter",
            "react native": "React Native",
        }

        normalized = set()
        for tech in tech_stack:
            if tech:
                clean = tech.strip().lower()
                # Use mapping or capitalize
                mapped = TECH_MAP.get(clean, tech.strip().title())
                normalized.add(mapped)
        return sorted(list(normalized))[:15]

    def _extract_industries(self, raw: RawOpportunity) -> List[str]:
        """Extract industry categories from raw data."""
        industries = set()
        combined = f"{raw.title} {raw.description or ''} {' '.join(raw.tags)}".lower()

        INDUSTRY_KEYWORDS = {
            "healthcare": ["health", "medical", "healthcare", "hospital", "patient"],
            "fintech": ["finance", "fintech", "banking", "payment", "crypto", "defi"],
            "edtech": ["education", "learning", "school", "student", "edtech"],
            "climate": ["climate", "sustainability", "green", "environment", "carbon"],
            "social impact": ["social", "nonprofit", "charity", "community", "impact"],
            "gaming": ["game", "gaming", "esports", "metaverse"],
            "ecommerce": ["ecommerce", "retail", "shopping", "marketplace"],
            "enterprise": ["enterprise", "b2b", "saas", "productivity"],
            "consumer": ["consumer", "b2c", "lifestyle", "social media"],
            "developer tools": ["developer", "devtools", "api", "infrastructure"],
        }

        for industry, keywords in INDUSTRY_KEYWORDS.items():
            if any(kw in combined for kw in keywords):
                industries.add(industry)

        return sorted(list(industries))[:5]

    def _extract_locales(self, raw: RawOpportunity) -> List[str]:
        """Extract locale/language information."""
        locales = ["en"]  # Default to English
        combined = f"{raw.title} {raw.description or ''}".lower()

        if any(word in combined for word in ["中文", "chinese", "中国"]):
            locales.append("zh")
        if any(word in combined for word in ["español", "spanish", "latam"]):
            locales.append("es")
        if any(word in combined for word in ["français", "french"]):
            locales.append("fr")

        return locales

    def _normalize_regions(
        self, regions: List[str], location: Optional[str]
    ) -> List[str]:
        """Normalize region information."""
        normalized = set()

        # Process provided regions
        for region in regions:
            if region:
                normalized.add(region.strip())

        # Parse location string
        if location:
            loc_lower = location.lower()
            if "online" in loc_lower or "virtual" in loc_lower or "remote" in loc_lower:
                normalized.add("Global")
            elif "worldwide" in loc_lower or "global" in loc_lower:
                normalized.add("Global")
            else:
                # Try to extract country/region
                normalized.add(location.strip())

        return sorted(list(normalized))[:10]

    def _extract_year(self, raw: RawOpportunity) -> Optional[int]:
        """Extract year from raw data."""
        # Try from dates
        for date_str in [raw.start_date, raw.end_date, raw.submission_deadline]:
            if date_str:
                try:
                    dt = date_parser.parse(date_str, fuzzy=True)
                    return dt.year
                except:
                    pass

        # Try from title
        year_match = re.search(r"20\d{2}", raw.title)
        if year_match:
            return int(year_match.group())

        return datetime.utcnow().year

    def _extract_season(self, raw: RawOpportunity) -> Optional[str]:
        """Extract season from raw data."""
        combined = f"{raw.title} {raw.description or ''}".lower()

        if any(word in combined for word in ["spring", "q1", "q2"]):
            return "spring"
        elif any(word in combined for word in ["summer"]):
            return "summer"
        elif any(word in combined for word in ["fall", "autumn", "q3", "q4"]):
            return "fall"
        elif any(word in combined for word in ["winter"]):
            return "winter"

        # Try to determine from date
        for date_str in [raw.start_date, raw.submission_deadline]:
            if date_str:
                try:
                    dt = date_parser.parse(date_str, fuzzy=True)
                    month = dt.month
                    if month in [3, 4, 5]:
                        return "spring"
                    elif month in [6, 7, 8]:
                        return "summer"
                    elif month in [9, 10, 11]:
                        return "fall"
                    else:
                        return "winter"
                except:
                    pass

        return None

    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string to datetime object."""
        if not date_str:
            return None

        try:
            # Try dateutil parser first
            dt = date_parser.parse(date_str, fuzzy=True)

            # Ensure timezone awareness
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=ZoneInfo("UTC"))

            return dt
        except Exception as e:
            logger.debug(f"Failed to parse date '{date_str}': {e}")
            return None

    def _extract_timezone(self, raw: RawOpportunity) -> str:
        """Extract timezone from raw data."""
        combined = f"{raw.title} {raw.description or ''} {raw.location or ''}"

        for abbr, tz in self.TIMEZONE_MAP.items():
            if abbr in combined.upper():
                return tz

        return "UTC"

    def _determine_status(self, raw: RawOpportunity) -> str:
        """Determine opportunity status based on dates."""
        now = datetime.utcnow()

        deadline = self._parse_datetime(raw.submission_deadline or raw.end_date)
        start = self._parse_datetime(raw.start_date)

        if deadline:
            deadline_naive = deadline.replace(tzinfo=None)
            if deadline_naive < now:
                return "ended"

        if start:
            start_naive = start.replace(tzinfo=None)
            if start_naive <= now:
                return "active"

        return "upcoming"

    def _extract_sponsors(self, raw: RawOpportunity) -> List[str]:
        """Extract sponsor information."""
        sponsors = []

        # Check raw_data for sponsor info
        if "sponsors" in raw.raw_data:
            sponsors.extend(raw.raw_data["sponsors"])

        # Check host
        if raw.host_name and raw.host_name not in sponsors:
            sponsors.append(raw.host_name)

        return sponsors[:10]

    def _normalize_prizes(self, raw: RawOpportunity) -> List[dict]:
        """Normalize prize information."""
        normalized = []

        for prize in raw.prizes:
            prize_data = {
                "prize_type": prize.get("type", "prize"),
                "name": prize.get("name", "Prize"),
                "amount": self._parse_prize_amount(prize.get("amount")),
                "currency": prize.get("currency", raw.prize_currency),
                "benefits": prize.get("benefits", []),
            }
            normalized.append(prize_data)

        # If no prizes but total amount is known
        if not normalized and raw.total_prize_amount:
            normalized.append(
                {
                    "prize_type": "total",
                    "name": "Total Prizes",
                    "amount": raw.total_prize_amount,
                    "currency": raw.prize_currency,
                    "benefits": [],
                }
            )

        return normalized

    def _parse_prize_amount(self, amount) -> Optional[float]:
        """Parse prize amount from various formats."""
        if amount is None:
            return None

        if isinstance(amount, (int, float)):
            return float(amount)

        if isinstance(amount, str):
            # Remove currency symbols and commas
            clean = re.sub(r"[^\d.]", "", amount)
            try:
                return float(clean) if clean else None
            except ValueError:
                return None

        return None
