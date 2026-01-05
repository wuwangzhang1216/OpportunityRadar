"""Integration tests for embedding service."""

import pytest


class TestEmbeddingServiceIntegration:
    """Integration tests for embedding service with OpenAI API.

    Note: These tests require OPENAI_API_KEY to be set.
    """

    @pytest.fixture
    def embedding_service(self):
        """Get embedding service instance."""
        from src.opportunity_radar.services import get_embedding_service

        return get_embedding_service()

    def test_single_embedding_generation(self, embedding_service):
        """Test generating a single embedding."""
        text = "A hackathon focused on AI and machine learning with Python"
        embedding = embedding_service.get_embedding(text)

        assert embedding is not None
        assert len(embedding) == 1536  # text-embedding-3-small dimension
        assert all(isinstance(x, float) for x in embedding)

    def test_batch_embedding_generation(self, embedding_service):
        """Test generating batch embeddings."""
        texts = [
            "Web development with React and Node.js",
            "Blockchain and cryptocurrency projects",
            "Mobile app development for iOS and Android",
        ]
        embeddings = embedding_service.get_embeddings_batch(texts)

        assert len(embeddings) == 3
        assert all(len(e) == 1536 for e in embeddings)

    def test_empty_text_raises_error(self, embedding_service):
        """Test that empty text raises an error."""
        with pytest.raises(ValueError):
            embedding_service.get_embedding("")

    def test_empty_batch_returns_empty(self, embedding_service):
        """Test that empty batch returns empty list."""
        embeddings = embedding_service.get_embeddings_batch([])
        assert embeddings == []

    def test_opportunity_embedding_generation(self, embedding_service):
        """Test generating embedding for opportunity."""
        result = embedding_service.generate_opportunity_embedding(
            opportunity_id="test-123",
            title="AI Hackathon 2024",
            description="Build innovative AI solutions for real-world problems",
            tags=["AI", "ML", "Deep Learning"],
            tech_stack=["Python", "TensorFlow", "PyTorch"],
            category="hackathon",
        )

        assert result.success is True
        assert result.id == "test-123"
        assert len(result.embedding) == 1536
        assert result.text_length > 0
