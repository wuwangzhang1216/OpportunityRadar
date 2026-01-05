"""Embedding service for semantic search and matching."""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from openai import OpenAI

from ..config import get_settings

logger = logging.getLogger(__name__)

# text-embedding-3-small outputs 1536 dimensions by default
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536

# OpenAI API limits
MAX_BATCH_SIZE = 2048  # Maximum texts per batch request
MAX_TOKENS_PER_REQUEST = 8191  # Maximum tokens per text


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""

    id: str
    embedding: List[float]
    text_length: int
    success: bool = True
    error: Optional[str] = None


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
        bio: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> str:
        """
        Create a rich text representation of a profile for embedding.

        The text is structured to maximize semantic similarity with relevant opportunities.
        Bio/description is the most important signal as it contains the actual project context.

        Args:
            tech_stack: List of technologies
            industries: List of industries/domains
            intents: List of goals (funding, learning, etc.)
            profile_type: Type of profile (student, startup, etc.)
            stage: Startup stage if applicable
            bio: Project/company description - PRIMARY signal
            display_name: Project/company name

        Returns:
            Combined text for embedding
        """
        parts = []

        # Bio is the most important - put it first for embedding models
        if bio:
            parts.append(bio[:1500])

        if display_name:
            parts.append(f"Project: {display_name}")

        if profile_type:
            parts.append(f"Type: {profile_type}")

        if stage:
            parts.append(f"Stage: {stage}")

        if tech_stack:
            # Expand common abbreviations for better semantic matching
            expanded_tech = self._expand_tech_terms(tech_stack)
            parts.append(f"Built with: {', '.join(expanded_tech)}")

        if industries:
            parts.append(f"Domain: {', '.join(industries)}")

        if intents:
            # Map goals to more descriptive phrases
            goal_phrases = self._expand_goals(intents)
            parts.append(f"Looking for: {', '.join(goal_phrases)}")

        return " ".join(parts) if parts else "General developer profile"

    def _expand_tech_terms(self, tech_stack: List[str]) -> List[str]:
        """Expand tech abbreviations for better embedding matching."""
        expansions = {
            "js": "JavaScript",
            "ts": "TypeScript",
            "py": "Python",
            "ml": "Machine Learning",
            "ai": "Artificial Intelligence",
            "llm": "Large Language Model",
            "db": "Database",
            "api": "API backend",
            "ui": "User Interface",
            "ux": "User Experience",
        }
        result = []
        for tech in tech_stack:
            lower = tech.lower()
            if lower in expansions:
                result.append(expansions[lower])
            else:
                result.append(tech)
        return result

    def _expand_goals(self, goals: List[str]) -> List[str]:
        """Expand goals to more descriptive phrases for embedding."""
        expansions = {
            "funding": "funding and investment opportunities",
            "prizes": "competitions with cash prizes",
            "learning": "learning new skills and technologies",
            "networking": "networking and meeting collaborators",
            "exposure": "visibility and user acquisition",
            "mentorship": "mentorship and guidance from experts",
            "building": "building and shipping products at hackathons",
            "equity": "equity-based accelerator programs",
        }
        return [expansions.get(g.lower(), g) for g in goals]

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

    def generate_opportunity_embedding(
        self,
        opportunity_id: str,
        title: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        tech_stack: Optional[List[str]] = None,
        industry: Optional[List[str]] = None,
        category: Optional[str] = None,
    ) -> EmbeddingResult:
        """
        Generate embedding for a single opportunity.

        Args:
            opportunity_id: Unique ID of the opportunity
            title: Opportunity title
            description: Full description
            tags: List of tags
            tech_stack: Required technologies
            industry: Related industries
            category: Opportunity category

        Returns:
            EmbeddingResult with embedding vector or error
        """
        try:
            text = self.create_opportunity_embedding_text(
                title=title,
                description=description,
                tags=tags,
                tech_stack=tech_stack,
                industry=industry,
                category=category,
            )
            embedding = self.get_embedding(text)
            return EmbeddingResult(
                id=opportunity_id,
                embedding=embedding,
                text_length=len(text),
                success=True,
            )
        except Exception as e:
            logger.error(f"Failed to generate embedding for opportunity {opportunity_id}: {e}")
            return EmbeddingResult(
                id=opportunity_id,
                embedding=[],
                text_length=0,
                success=False,
                error=str(e),
            )

    def generate_opportunity_embeddings_batch(
        self,
        opportunities: List[Dict],
        batch_size: int = 100,
    ) -> Tuple[List[EmbeddingResult], Dict]:
        """
        Generate embeddings for multiple opportunities in batches.

        Args:
            opportunities: List of opportunity dicts with keys:
                - id: Opportunity ID
                - title: Title
                - description: Description (optional)
                - tags: List of tags (optional)
                - tech_stack/technologies: List of technologies (optional)
                - industry/themes: List of industries (optional)
                - category/opportunity_type: Category (optional)
            batch_size: Number of opportunities per batch (default 100)

        Returns:
            Tuple of (results list, stats dict)
        """
        results = []
        stats = {
            "total": len(opportunities),
            "success": 0,
            "failed": 0,
            "skipped": 0,
        }

        if not opportunities:
            return results, stats

        # Process in batches
        for i in range(0, len(opportunities), batch_size):
            batch = opportunities[i : i + batch_size]

            # Prepare texts and IDs
            texts = []
            ids = []
            text_lengths = []

            for opp in batch:
                opp_id = opp.get("id") or opp.get("_id")
                if not opp_id:
                    stats["skipped"] += 1
                    continue

                title = opp.get("title", "")
                if not title:
                    stats["skipped"] += 1
                    results.append(
                        EmbeddingResult(
                            id=str(opp_id),
                            embedding=[],
                            text_length=0,
                            success=False,
                            error="Missing title",
                        )
                    )
                    continue

                # Handle different field naming conventions
                description = opp.get("description") or opp.get("short_description")
                tags = opp.get("tags") or opp.get("themes", [])
                tech_stack = opp.get("tech_stack") or opp.get("technologies", [])
                industry = opp.get("industry") or opp.get("themes", [])
                category = opp.get("category") or opp.get("opportunity_type")

                text = self.create_opportunity_embedding_text(
                    title=title,
                    description=description,
                    tags=tags,
                    tech_stack=tech_stack,
                    industry=industry,
                    category=category,
                )

                texts.append(text)
                ids.append(str(opp_id))
                text_lengths.append(len(text))

            if not texts:
                continue

            # Generate embeddings for batch
            try:
                embeddings = self.get_embeddings_batch(texts)

                for j, embedding in enumerate(embeddings):
                    results.append(
                        EmbeddingResult(
                            id=ids[j],
                            embedding=embedding,
                            text_length=text_lengths[j],
                            success=True,
                        )
                    )
                    stats["success"] += 1

            except Exception as e:
                logger.error(f"Batch embedding failed: {e}")
                # Mark all in this batch as failed
                for j in range(len(texts)):
                    results.append(
                        EmbeddingResult(
                            id=ids[j],
                            embedding=[],
                            text_length=text_lengths[j],
                            success=False,
                            error=str(e),
                        )
                    )
                    stats["failed"] += 1

            logger.info(
                f"Processed batch {i // batch_size + 1}: "
                f"{stats['success']} success, {stats['failed']} failed"
            )

        return results, stats


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the embedding service singleton."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
