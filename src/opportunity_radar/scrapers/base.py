"""Base scraper interface and common utilities."""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, AsyncIterator, Callable, List, Optional, TypeVar

import httpx

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ScraperStatus(str, Enum):
    """Scraper execution status."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class RawOpportunity:
    """Raw scraped opportunity data before normalization."""

    source: str
    external_id: str
    title: str
    url: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    raw_data: dict = field(default_factory=dict)

    # Timeline fields (raw strings, to be parsed)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    submission_deadline: Optional[str] = None
    registration_deadline: Optional[str] = None

    # Location/format
    location: Optional[str] = None
    is_online: bool = True
    regions: List[str] = field(default_factory=list)

    # Team requirements
    team_min: Optional[int] = None
    team_max: Optional[int] = None

    # Prizes
    prizes: List[dict] = field(default_factory=list)
    total_prize_amount: Optional[float] = None
    prize_currency: str = "USD"

    # Tags and categories
    tags: List[str] = field(default_factory=list)
    themes: List[str] = field(default_factory=list)
    tech_stack: List[str] = field(default_factory=list)

    # Host info
    host_name: Optional[str] = None
    host_url: Optional[str] = None

    # Requirements
    eligibility_rules: List[dict] = field(default_factory=list)
    student_only: bool = False


@dataclass
class ScraperResult:
    """Result of a scraping operation."""

    opportunities: List[RawOpportunity]
    status: ScraperStatus
    source: str
    scraped_at: datetime = field(default_factory=datetime.utcnow)
    total_found: int = 0
    error_message: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.status in (ScraperStatus.SUCCESS, ScraperStatus.PARTIAL)


def with_retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    exceptions: tuple = (httpx.HTTPError, asyncio.TimeoutError, ConnectionError),
):
    """Decorator for retry logic with exponential backoff."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = backoff_factor**attempt
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"All {max_attempts} attempts failed: {e}")
            raise last_exception

        return wrapper

    return decorator


class CircuitBreaker:
    """Simple circuit breaker for source availability."""

    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: int = 300,
        half_open_max_calls: int = 3,
    ):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_max_calls = half_open_max_calls
        self.failures = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed, open, half-open
        self.half_open_calls = 0

    def can_execute(self) -> bool:
        """Check if request can be executed."""
        if self.state == "closed":
            return True
        elif self.state == "open":
            if self.last_failure_time:
                elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if elapsed >= self.reset_timeout:
                    self.state = "half-open"
                    self.half_open_calls = 0
                    return True
            return False
        else:  # half-open
            return self.half_open_calls < self.half_open_max_calls

    def record_success(self):
        """Record successful call."""
        if self.state == "half-open":
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                self.state = "closed"
                self.failures = 0
        elif self.state == "closed":
            self.failures = 0

    def record_failure(self):
        """Record failed call."""
        self.failures += 1
        self.last_failure_time = datetime.utcnow()
        if self.failures >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failures} failures")


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    def __init__(
        self,
        request_delay: float = 2.0,
        timeout: float = 30.0,
        max_pages: int = 50,
    ):
        self.request_delay = request_delay
        self.timeout = timeout
        self.max_pages = max_pages
        self.circuit_breaker = CircuitBreaker()
        self._client: Optional[httpx.AsyncClient] = None

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique identifier for this source."""
        pass

    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base URL for the source."""
        pass

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                },
                follow_redirects=True,
            )
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    @abstractmethod
    async def scrape_list(self, page: int = 1) -> ScraperResult:
        """Scrape list of opportunities from a page."""
        pass

    @abstractmethod
    async def scrape_detail(self, external_id: str, url: str) -> Optional[RawOpportunity]:
        """Scrape detailed information for a single opportunity."""
        pass

    async def scrape_all(self, max_pages: Optional[int] = None) -> ScraperResult:
        """Scrape all available opportunities."""
        max_pages = max_pages or self.max_pages
        all_opportunities: List[RawOpportunity] = []
        errors: List[str] = []
        page = 1

        while page <= max_pages:
            if not self.circuit_breaker.can_execute():
                logger.warning(f"Circuit breaker open for {self.source_name}")
                break

            try:
                result = await self.scrape_list(page)

                if result.success:
                    self.circuit_breaker.record_success()
                    all_opportunities.extend(result.opportunities)

                    if not result.opportunities:
                        # No more results
                        break

                    logger.info(
                        f"[{self.source_name}] Page {page}: {len(result.opportunities)} opportunities"
                    )
                else:
                    self.circuit_breaker.record_failure()
                    errors.append(f"Page {page}: {result.error_message}")

                page += 1
                await asyncio.sleep(self.request_delay)

            except Exception as e:
                self.circuit_breaker.record_failure()
                errors.append(f"Page {page}: {str(e)}")
                logger.error(f"[{self.source_name}] Error on page {page}: {e}")
                break

        status = ScraperStatus.SUCCESS
        if errors:
            status = ScraperStatus.PARTIAL if all_opportunities else ScraperStatus.FAILED

        return ScraperResult(
            opportunities=all_opportunities,
            status=status,
            source=self.source_name,
            total_found=len(all_opportunities),
            errors=errors,
            error_message="; ".join(errors) if errors else None,
        )

    async def health_check(self) -> bool:
        """Check if source is accessible."""
        try:
            client = await self.get_client()
            response = await client.head(self.base_url)
            return response.status_code < 400
        except Exception as e:
            logger.error(f"Health check failed for {self.source_name}: {e}")
            return False

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} source={self.source_name}>"
