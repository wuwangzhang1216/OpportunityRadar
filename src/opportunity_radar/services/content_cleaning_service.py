"""Content cleaning service using LLM to reformat scraped content."""

import json
import logging
from typing import Optional

from openai import OpenAI

from ..config import get_settings

logger = logging.getLogger(__name__)


def clean_description_with_llm(raw_description: str) -> str:
    """
    Clean and reformat a scraped description using OpenAI.

    Args:
        raw_description: The raw scraped description text

    Returns:
        Cleaned and reformatted description
    """
    if not raw_description or len(raw_description) < 50:
        return raw_description

    try:
        settings = get_settings()
        client = OpenAI(api_key=settings.openai_api_key)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """Clean this hackathon/opportunity description:
1. Merge fragmented lines into proper paragraphs
2. Keep section headers on separate lines
3. Format lists with - bullets
4. Preserve all important information
5. Output JSON: {"description": "cleaned text"}""",
                },
                {"role": "user", "content": raw_description[:3500]},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=2500,
        )

        result = json.loads(response.choices[0].message.content)
        return result.get("description", raw_description)

    except Exception as e:
        logger.error(f"Failed to clean description with LLM: {e}")
        return raw_description


async def clean_description(raw_description: str) -> str:
    """Async wrapper for clean_description_with_llm."""
    return clean_description_with_llm(raw_description)
