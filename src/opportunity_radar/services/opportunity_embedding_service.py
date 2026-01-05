"""Service for generating and managing opportunity embeddings."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from openai import OpenAI

from ..config import get_settings
from ..models.opportunity import Opportunity

logger = logging.getLogger(__name__)

# OpenAI embedding model
EMBEDDING_MODEL = "text-embedding-3-small"


class OpportunityEmbeddingService:
    """Service for generating embeddings for opportunities using OpenAI."""

    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = EMBEDDING_MODEL

    def _create_embedding_text(self, opportunity: Opportunity) -> str:
        """Create text representation of opportunity for embedding."""
        parts = [opportunity.title]

        if opportunity.opportunity_type:
            parts.append(f"Type: {opportunity.opportunity_type}")

        if opportunity.description:
            # Truncate to first 2000 chars
            parts.append(opportunity.description[:2000])

        if opportunity.themes:
            parts.append(f"Themes: {', '.join(opportunity.themes)}")

        if opportunity.technologies:
            parts.append(f"Technologies: {', '.join(opportunity.technologies)}")

        if opportunity.format:
            parts.append(f"Format: {opportunity.format}")

        return ". ".join(parts)

    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI."""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Truncate if too long
        text = text[:8000]

        response = self.client.embeddings.create(
            input=text,
            model=self.model,
        )
        return response.data[0].embedding

    async def generate_embedding_for_opportunity(
        self,
        opportunity_id: str,
    ) -> bool:
        """
        Generate and save embedding for a single opportunity.

        Args:
            opportunity_id: The opportunity ID

        Returns:
            True if successful, False otherwise
        """
        from beanie import PydanticObjectId

        try:
            opportunity = await Opportunity.get(PydanticObjectId(opportunity_id))
            if not opportunity:
                logger.warning(f"Opportunity {opportunity_id} not found")
                return False

            text = self._create_embedding_text(opportunity)
            embedding = self._get_embedding(text)

            opportunity.embedding = embedding
            opportunity.updated_at = datetime.utcnow()
            await opportunity.save()

            logger.info(f"Generated embedding for opportunity: {opportunity.title}")
            return True

        except Exception as e:
            logger.error(f"Failed to generate embedding for {opportunity_id}: {e}")
            return False

    async def generate_embeddings_batch(
        self,
        opportunity_ids: Optional[List[str]] = None,
        batch_size: int = 100,
        only_missing: bool = True,
    ) -> Dict:
        """
        Generate embeddings for multiple opportunities.

        Args:
            opportunity_ids: Specific IDs to process (None = all)
            batch_size: Number to process at once
            only_missing: Only process opportunities without embeddings

        Returns:
            Statistics about the operation
        """
        from beanie import PydanticObjectId

        stats = {
            "total": 0,
            "processed": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
        }

        # Build query
        if opportunity_ids:
            oids = [PydanticObjectId(oid) for oid in opportunity_ids]
            opportunities = await Opportunity.find(
                {"_id": {"$in": oids}}
            ).to_list()
        elif only_missing:
            opportunities = await Opportunity.find(
                {"embedding": None}
            ).to_list()
        else:
            opportunities = await Opportunity.find_all().to_list()

        stats["total"] = len(opportunities)
        logger.info(f"Processing {stats['total']} opportunities for embeddings")

        # Process in batches
        for i in range(0, len(opportunities), batch_size):
            batch = opportunities[i:i + batch_size]
            texts = []
            valid_opps = []

            for opp in batch:
                # Skip if already has embedding and only_missing is True
                if only_missing and opp.embedding:
                    stats["skipped"] += 1
                    continue

                try:
                    text = self._create_embedding_text(opp)
                    texts.append(text)
                    valid_opps.append(opp)
                except Exception as e:
                    logger.warning(f"Failed to create text for {opp.id}: {e}")
                    stats["failed"] += 1

            if not texts:
                continue

            # Generate embeddings in batch
            try:
                response = self.client.embeddings.create(
                    input=texts,
                    model=self.model,
                )

                # Sort by index to maintain order
                sorted_data = sorted(response.data, key=lambda x: x.index)

                for j, embedding_data in enumerate(sorted_data):
                    try:
                        valid_opps[j].embedding = embedding_data.embedding
                        valid_opps[j].updated_at = datetime.utcnow()
                        await valid_opps[j].save()
                        stats["success"] += 1
                    except Exception as e:
                        logger.error(f"Failed to save embedding for {valid_opps[j].id}: {e}")
                        stats["failed"] += 1

                stats["processed"] += len(texts)

            except Exception as e:
                logger.error(f"Batch embedding failed: {e}")
                stats["failed"] += len(texts)

            logger.info(
                f"Processed batch {i // batch_size + 1}: "
                f"{stats['success']} success, {stats['failed']} failed"
            )

        return stats

    async def get_opportunities_without_embeddings(
        self,
        limit: int = 100,
    ) -> List[Dict]:
        """Get opportunities that don't have embeddings yet."""
        opportunities = await Opportunity.find(
            {"embedding": None}
        ).limit(limit).to_list()

        return [
            {
                "id": str(opp.id),
                "title": opp.title,
                "type": opp.opportunity_type,
            }
            for opp in opportunities
        ]

    async def get_embedding_stats(self) -> Dict:
        """Get statistics about opportunity embeddings."""
        total = await Opportunity.count()
        with_embedding = await Opportunity.find(
            {"embedding": {"$ne": None}}
        ).count()

        return {
            "total_opportunities": total,
            "with_embeddings": with_embedding,
            "without_embeddings": total - with_embedding,
            "coverage_percent": round(with_embedding / total * 100, 1) if total > 0 else 0,
        }


# Singleton instance
_service: Optional[OpportunityEmbeddingService] = None


def get_opportunity_embedding_service() -> OpportunityEmbeddingService:
    """Get or create the opportunity embedding service singleton."""
    global _service
    if _service is None:
        _service = OpportunityEmbeddingService()
    return _service
