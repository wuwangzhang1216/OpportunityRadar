"""LLM-based structured data extraction for scraped content."""

import logging
from typing import Optional, List

from pydantic import BaseModel, Field
from openai import OpenAI

from ..config import get_settings

logger = logging.getLogger(__name__)


class ExtractedPrize(BaseModel):
    """Extracted prize information."""
    name: str = Field(description="Prize name/title, e.g. 'Grand Prize', 'Winner', '1st Place'")
    amount: Optional[float] = Field(None, description="Prize amount as a number, e.g. 75 for '$75', 1000 for '$1,000'")
    currency: str = Field(default="USD", description="Currency code")
    description: Optional[str] = Field(None, description="Additional prize details")


class ExtractedOpportunityData(BaseModel):
    """Structured data extracted from opportunity page."""
    title: Optional[str] = Field(None, description="The title of the hackathon/opportunity")
    description: Optional[str] = Field(None, description="Brief description (first 500 chars)")
    prizes: List[ExtractedPrize] = Field(default_factory=list, description="List of prizes")
    total_prize_value: Optional[float] = Field(None, description="Total prize pool amount as a number")
    themes: List[str] = Field(default_factory=list, description="Themes/categories like 'AI', 'Web3'")
    technologies: List[str] = Field(default_factory=list, description="Required technologies like 'Python', 'React'")
    team_size_min: Optional[int] = Field(None, description="Minimum team size")
    team_size_max: Optional[int] = Field(None, description="Maximum team size")
    is_student_only: bool = Field(default=False, description="Whether restricted to students")
    eligibility_requirements: List[str] = Field(default_factory=list, description="List of eligibility criteria")
    start_date: Optional[str] = Field(None, description="Event start date")
    end_date: Optional[str] = Field(None, description="Event end date")
    submission_deadline: Optional[str] = Field(None, description="Submission deadline")
    location: Optional[str] = Field(None, description="Event location or 'Online'")
    is_online: bool = Field(default=True, description="Whether it's online/virtual")


EXTRACTION_SYSTEM_PROMPT = """You are a data extraction assistant that extracts structured information from hackathon/opportunity pages.

IMPORTANT RULES FOR PRIZE AMOUNTS:
- Extract prize amounts as plain numbers WITHOUT any multiplier
- "$75" should be 75
- "$1,000" should be 1000
- "$50k" or "$50K" should be 50000
- "$1.5M" should be 1500000
- If a prize has no monetary value, set amount to null
- Be careful not to confuse descriptive text with prize amounts

For dates, use the original format from the page or ISO format (YYYY-MM-DD) when possible."""


def _get_openai_client() -> OpenAI:
    """Get OpenAI client."""
    settings = get_settings()
    return OpenAI(api_key=settings.openai_api_key)


async def extract_opportunity_data(
    html_content: str,
    page_text: Optional[str] = None,
    max_content_length: int = 8000,
) -> Optional[ExtractedOpportunityData]:
    """
    Use LLM with structured output to extract data from opportunity page.

    Args:
        html_content: Raw HTML content (will be converted to text if page_text not provided)
        page_text: Pre-extracted text content from the page
        max_content_length: Maximum content length to send to LLM

    Returns:
        ExtractedOpportunityData or None if extraction fails
    """
    try:
        # Use provided text or extract from HTML
        if page_text:
            content = page_text[:max_content_length]
        else:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, "lxml")
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()
            content = soup.get_text(separator="\n", strip=True)[:max_content_length]

        if not content or len(content) < 100:
            logger.warning("Content too short for extraction")
            return None

        client = _get_openai_client()

        # Use structured output with Pydantic model
        completion = client.chat.completions.parse(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": f"Extract structured information from this hackathon page:\n\n{content}"},
            ],
            response_format=ExtractedOpportunityData,
        )

        result = completion.choices[0].message

        # Handle refusal
        if result.refusal:
            logger.warning(f"Model refused to extract: {result.refusal}")
            return None

        return result.parsed

    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        return None


async def extract_prizes_from_text(prize_text: str) -> List[ExtractedPrize]:
    """
    Extract prize information from text using LLM structured output.

    Args:
        prize_text: Text containing prize information

    Returns:
        List of ExtractedPrize objects
    """
    if not prize_text or len(prize_text) < 10:
        return []

    try:
        client = _get_openai_client()

        class PrizeList(BaseModel):
            prizes: List[ExtractedPrize] = Field(description="List of extracted prizes")

        completion = client.chat.completions.parse(
            model="gpt-5-mini",
            messages=[
                {
                    "role": "system",
                    "content": """Extract prize information from text.
IMPORTANT: Extract exact dollar amounts as numbers.
- "$75" = 75
- "$50" = 50
- "$1,000" = 1000
- "$50k" = 50000"""
                },
                {"role": "user", "content": f"Extract prizes from:\n\n{prize_text[:3000]}"},
            ],
            response_format=PrizeList,
        )

        result = completion.choices[0].message

        if result.refusal:
            logger.warning(f"Model refused to extract prizes: {result.refusal}")
            return []

        return result.parsed.prizes if result.parsed else []

    except Exception as e:
        logger.error(f"Failed to extract prizes: {e}")
        return []
