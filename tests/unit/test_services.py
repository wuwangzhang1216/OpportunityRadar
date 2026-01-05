"""Unit tests for services."""

import pytest


class TestServiceImports:
    """Test that all services can be imported correctly."""

    def test_import_auth_service(self):
        """Test AuthService import."""
        from src.opportunity_radar.services import AuthService

        assert AuthService is not None

    def test_import_opportunity_service(self):
        """Test OpportunityService import."""
        from src.opportunity_radar.services import OpportunityService

        assert OpportunityService is not None

    def test_import_embedding_service(self):
        """Test EmbeddingService import."""
        from src.opportunity_radar.services import EmbeddingService

        assert EmbeddingService is not None

    def test_import_matching_service(self):
        """Test MatchingService import."""
        from src.opportunity_radar.services import MatchingService

        assert MatchingService is not None

    def test_import_profile_service(self):
        """Test ProfileService import."""
        from src.opportunity_radar.services import ProfileService

        assert ProfileService is not None

    def test_import_pipeline_service(self):
        """Test PipelineService import."""
        from src.opportunity_radar.services import PipelineService

        assert PipelineService is not None


class TestEmbeddingService:
    """Test EmbeddingService functionality."""

    def test_get_embedding_service_singleton(self):
        """Test embedding service singleton pattern."""
        from src.opportunity_radar.services import get_embedding_service

        service1 = get_embedding_service()
        service2 = get_embedding_service()
        assert service1 is service2

    def test_embedding_service_model(self):
        """Test embedding service uses correct model."""
        from src.opportunity_radar.services import get_embedding_service

        service = get_embedding_service()
        assert service.model == "text-embedding-3-small"

    def test_create_opportunity_embedding_text(self):
        """Test opportunity embedding text creation."""
        from src.opportunity_radar.services import get_embedding_service

        service = get_embedding_service()
        text = service.create_opportunity_embedding_text(
            title="AI Hackathon 2024",
            description="Build innovative AI solutions",
            tags=["AI", "ML"],
            tech_stack=["Python", "TensorFlow"],
            category="hackathon",
        )

        assert "AI Hackathon 2024" in text
        assert "hackathon" in text.lower()
        assert len(text) > 50

    def test_create_profile_embedding_text(self):
        """Test profile embedding text creation."""
        from src.opportunity_radar.services import get_embedding_service

        service = get_embedding_service()
        text = service.create_profile_embedding_text(
            tech_stack=["Python", "JavaScript"],
            industries=["FinTech", "Healthcare"],
            intents=["funding", "learning"],
            profile_type="developer",
        )

        assert "Python" in text
        assert "developer" in text.lower()
        assert len(text) > 30
