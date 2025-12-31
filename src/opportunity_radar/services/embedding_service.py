"""Embedding service for semantic search and matching."""

import logging
from typing import List, Optional

from openai import OpenAI

from ..config import get_settings

logger = logging.getLogger(__name__)

# text-embedding-3-small outputs 1536 dimensions by default
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536


class EmbeddingService:
    """Service for generating and managing text embeddings."""

    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = EMBEDDING_MODEL

    def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: The text to embed

        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Truncate if too long (model limit is ~8191 tokens)
        text = text[:8000]

        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.model,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in a batch.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Filter and truncate texts
        processed_texts = []
        for text in texts:
            if text and text.strip():
                processed_texts.append(text[:8000])

        if not processed_texts:
            return []

        try:
            response = self.client.embeddings.create(
                input=processed_texts,
                model=self.model,
            )
            # Sort by index to maintain order
            sorted_data = sorted(response.data, key=lambda x: x.index)
            return [item.embedding for item in sorted_data]
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise

    def create_profile_embedding_text(
        self,
        tech_stack: List[str],
        industries: List[str],
        intents: List[str],
        profile_type: Optional[str] = None,
        stage: Optional[str] = None,
    ) -> str:
        """
        Create a text representation of a profile for embedding.

        Args:
            tech_stack: List of technologies
            industries: List of industries/domains
            intents: List of goals (funding, learning, etc.)
            profile_type: Type of profile (student, startup, etc.)
            stage: Startup stage if applicable

        Returns:
            Combined text for embedding
        """
        parts = []

        if profile_type:
            parts.append(f"Profile type: {profile_type}")

        if stage:
            parts.append(f"Stage: {stage}")

        if tech_stack:
            parts.append(f"Technologies: {', '.join(tech_stack)}")

        if industries:
            parts.append(f"Industries: {', '.join(industries)}")

        if intents:
            parts.append(f"Goals: {', '.join(intents)}")

        return ". ".join(parts) if parts else "General developer profile"

    def create_opportunity_embedding_text(
        self,
        title: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        tech_stack: Optional[List[str]] = None,
        industry: Optional[List[str]] = None,
        category: Optional[str] = None,
    ) -> str:
        """
        Create a text representation of an opportunity for embedding.

        Args:
            title: Opportunity title
            description: Full description
            tags: List of tags
            tech_stack: Required technologies
            industry: Related industries
            category: Opportunity category

        Returns:
            Combined text for embedding
        """
        parts = [title]

        if category:
            parts.append(f"Category: {category}")

        if description:
            # Take first 2000 chars of description
            parts.append(description[:2000])

        if tags:
            parts.append(f"Tags: {', '.join(tags)}")

        if tech_stack:
            parts.append(f"Technologies: {', '.join(tech_stack)}")

        if industry:
            parts.append(f"Industries: {', '.join(industry)}")

        return ". ".join(parts)


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the embedding service singleton."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
