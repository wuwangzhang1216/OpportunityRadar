"""Comprehensive unit tests for EmbeddingService."""

import pytest
from unittest.mock import MagicMock, patch


class TestEmbeddingServiceStructure:
    """Test EmbeddingService class structure."""

    def test_embedding_service_import(self):
        """Test EmbeddingService can be imported."""
        from src.opportunity_radar.services.embedding_service import EmbeddingService
        assert EmbeddingService is not None

    def test_embedding_result_import(self):
        """Test EmbeddingResult can be imported."""
        from src.opportunity_radar.services.embedding_service import EmbeddingResult
        assert EmbeddingResult is not None

    def test_embedding_constants(self):
        """Test embedding constants are defined."""
        from src.opportunity_radar.services.embedding_service import (
            EMBEDDING_MODEL,
            EMBEDDING_DIMENSION,
            MAX_BATCH_SIZE,
            MAX_TOKENS_PER_REQUEST,
        )

        assert EMBEDDING_MODEL == "text-embedding-3-small"
        assert EMBEDDING_DIMENSION == 1536
        assert MAX_BATCH_SIZE == 2048
        assert MAX_TOKENS_PER_REQUEST == 8191

    def test_service_has_required_methods(self):
        """Test EmbeddingService has all required methods."""
        from src.opportunity_radar.services.embedding_service import EmbeddingService

        required_methods = [
            "get_embedding",
            "get_embeddings_batch",
            "create_profile_embedding_text",
            "create_opportunity_embedding_text",
            "generate_opportunity_embedding",
            "generate_opportunity_embeddings_batch",
        ]

        for method in required_methods:
            assert hasattr(EmbeddingService, method), f"Missing method: {method}"


class TestEmbeddingResult:
    """Test EmbeddingResult dataclass."""

    def test_embedding_result_creation(self):
        """Test EmbeddingResult creation."""
        from src.opportunity_radar.services.embedding_service import EmbeddingResult

        result = EmbeddingResult(
            id="test_id",
            embedding=[0.1, 0.2, 0.3],
            text_length=100,
            success=True,
        )

        assert result.id == "test_id"
        assert result.embedding == [0.1, 0.2, 0.3]
        assert result.text_length == 100
        assert result.success is True
        assert result.error is None

    def test_embedding_result_with_error(self):
        """Test EmbeddingResult with error."""
        from src.opportunity_radar.services.embedding_service import EmbeddingResult

        result = EmbeddingResult(
            id="test_id",
            embedding=[],
            text_length=0,
            success=False,
            error="API error",
        )

        assert result.success is False
        assert result.error == "API error"
        assert result.embedding == []

    def test_embedding_result_defaults(self):
        """Test EmbeddingResult default values."""
        from src.opportunity_radar.services.embedding_service import EmbeddingResult

        result = EmbeddingResult(
            id="test_id",
            embedding=[0.1],
            text_length=10,
        )

        assert result.success is True
        assert result.error is None


class TestCreateProfileEmbeddingText:
    """Test create_profile_embedding_text method."""

    def test_create_profile_text_basic(self):
        """Test basic profile text creation."""
        from src.opportunity_radar.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, "__init__", lambda self: None):
            service = EmbeddingService()
            service.client = MagicMock()
            service.model = "text-embedding-3-small"

            text = service.create_profile_embedding_text(
                tech_stack=["Python", "FastAPI"],
                industries=["AI/ML", "SaaS"],
                intents=["funding", "networking"],
            )

            assert "Python" in text
            assert "FastAPI" in text
            assert "AI/ML" in text or "Domain" in text

    def test_create_profile_text_with_bio(self):
        """Test profile text creation with bio."""
        from src.opportunity_radar.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, "__init__", lambda self: None):
            service = EmbeddingService()
            service.client = MagicMock()
            service.model = "text-embedding-3-small"

            text = service.create_profile_embedding_text(
                tech_stack=["Python"],
                industries=["AI"],
                intents=["learning"],
                bio="Building AI tools for developers",
            )

            # Bio should appear first
            assert text.startswith("Building AI tools")

    def test_create_profile_text_with_display_name(self):
        """Test profile text creation with display name."""
        from src.opportunity_radar.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, "__init__", lambda self: None):
            service = EmbeddingService()
            service.client = MagicMock()
            service.model = "text-embedding-3-small"

            text = service.create_profile_embedding_text(
                tech_stack=["Python"],
                industries=["AI"],
                intents=["learning"],
                display_name="My Cool Project",
            )

            assert "My Cool Project" in text

    def test_create_profile_text_empty(self):
        """Test profile text creation with empty inputs."""
        from src.opportunity_radar.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, "__init__", lambda self: None):
            service = EmbeddingService()
            service.client = MagicMock()
            service.model = "text-embedding-3-small"

            text = service.create_profile_embedding_text(
                tech_stack=[],
                industries=[],
                intents=[],
            )

            assert text == "General developer profile"


class TestExpandTechTerms:
    """Test _expand_tech_terms method."""

    def test_expand_common_abbreviations(self):
        """Test expansion of common tech abbreviations."""
        from src.opportunity_radar.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, "__init__", lambda self: None):
            service = EmbeddingService()
            service.client = MagicMock()
            service.model = "text-embedding-3-small"

            result = service._expand_tech_terms(["js", "ts", "py", "ml"])

            assert "JavaScript" in result
            assert "TypeScript" in result
            assert "Python" in result
            assert "Machine Learning" in result

    def test_expand_preserves_unknown(self):
        """Test expansion preserves unknown terms."""
        from src.opportunity_radar.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, "__init__", lambda self: None):
            service = EmbeddingService()
            service.client = MagicMock()
            service.model = "text-embedding-3-small"

            result = service._expand_tech_terms(["React", "Vue", "Unknown"])

            assert "React" in result
            assert "Vue" in result
            assert "Unknown" in result


class TestExpandGoals:
    """Test _expand_goals method."""

    def test_expand_known_goals(self):
        """Test expansion of known goals."""
        from src.opportunity_radar.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, "__init__", lambda self: None):
            service = EmbeddingService()
            service.client = MagicMock()
            service.model = "text-embedding-3-small"

            result = service._expand_goals(["funding", "networking", "learning"])

            assert any("funding" in r.lower() for r in result)
            assert any("networking" in r.lower() or "collaborator" in r.lower() for r in result)

    def test_expand_preserves_unknown_goals(self):
        """Test expansion preserves unknown goals."""
        from src.opportunity_radar.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, "__init__", lambda self: None):
            service = EmbeddingService()
            service.client = MagicMock()
            service.model = "text-embedding-3-small"

            result = service._expand_goals(["custom_goal"])

            assert "custom_goal" in result


class TestCreateOpportunityEmbeddingText:
    """Test create_opportunity_embedding_text method."""

    def test_create_opportunity_text_basic(self):
        """Test basic opportunity text creation."""
        from src.opportunity_radar.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, "__init__", lambda self: None):
            service = EmbeddingService()
            service.client = MagicMock()
            service.model = "text-embedding-3-small"

            text = service.create_opportunity_embedding_text(
                title="AI Hackathon 2024",
            )

            assert "AI Hackathon 2024" in text

    def test_create_opportunity_text_with_all_fields(self):
        """Test opportunity text creation with all fields."""
        from src.opportunity_radar.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, "__init__", lambda self: None):
            service = EmbeddingService()
            service.client = MagicMock()
            service.model = "text-embedding-3-small"

            text = service.create_opportunity_embedding_text(
                title="AI Hackathon",
                description="Build AI applications",
                tags=["AI", "ML"],
                tech_stack=["Python", "TensorFlow"],
                industry=["Healthcare", "Finance"],
                category="hackathon",
            )

            assert "AI Hackathon" in text
            assert "Build AI applications" in text
            assert "Python" in text or "Technologies" in text

    def test_create_opportunity_text_truncates_description(self):
        """Test opportunity text truncates long description."""
        from src.opportunity_radar.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, "__init__", lambda self: None):
            service = EmbeddingService()
            service.client = MagicMock()
            service.model = "text-embedding-3-small"

            long_description = "A" * 5000
            text = service.create_opportunity_embedding_text(
                title="Test",
                description=long_description,
            )

            # Description should be truncated to 2000 chars
            assert len(text) < 5000


class TestGetEmbedding:
    """Test get_embedding method."""

    def test_get_embedding_empty_text_raises(self):
        """Test get_embedding raises for empty text."""
        from src.opportunity_radar.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, "__init__", lambda self: None):
            service = EmbeddingService()
            service.client = MagicMock()
            service.model = "text-embedding-3-small"

            with pytest.raises(ValueError):
                service.get_embedding("")

    def test_get_embedding_whitespace_raises(self):
        """Test get_embedding raises for whitespace-only text."""
        from src.opportunity_radar.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, "__init__", lambda self: None):
            service = EmbeddingService()
            service.client = MagicMock()
            service.model = "text-embedding-3-small"

            with pytest.raises(ValueError):
                service.get_embedding("   ")

    def test_get_embedding_success(self):
        """Test get_embedding returns embedding on success."""
        from src.opportunity_radar.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, "__init__", lambda self: None):
            service = EmbeddingService()
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
            mock_client.embeddings.create.return_value = mock_response

            service.client = mock_client
            service.model = "text-embedding-3-small"

            result = service.get_embedding("test text")

            assert result == [0.1, 0.2, 0.3]

    def test_get_embedding_truncates_long_text(self):
        """Test get_embedding truncates text longer than 8000 chars."""
        from src.opportunity_radar.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, "__init__", lambda self: None):
            service = EmbeddingService()
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.data = [MagicMock(embedding=[0.1])]
            mock_client.embeddings.create.return_value = mock_response

            service.client = mock_client
            service.model = "text-embedding-3-small"

            long_text = "A" * 10000
            service.get_embedding(long_text)

            # Verify the text was truncated
            called_text = mock_client.embeddings.create.call_args[1]["input"]
            assert len(called_text) == 8000


class TestGetEmbeddingsBatch:
    """Test get_embeddings_batch method."""

    def test_batch_empty_list(self):
        """Test batch embedding with empty list."""
        from src.opportunity_radar.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, "__init__", lambda self: None):
            service = EmbeddingService()
            service.client = MagicMock()
            service.model = "text-embedding-3-small"

            result = service.get_embeddings_batch([])

            assert result == []

    def test_batch_filters_empty_texts(self):
        """Test batch embedding filters empty texts."""
        from src.opportunity_radar.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, "__init__", lambda self: None):
            service = EmbeddingService()
            service.client = MagicMock()
            service.model = "text-embedding-3-small"

            result = service.get_embeddings_batch(["", "  ", None])

            # All texts filtered out
            assert result == []

    def test_batch_preserves_order(self):
        """Test batch embedding preserves order."""
        from src.opportunity_radar.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, "__init__", lambda self: None):
            service = EmbeddingService()
            mock_client = MagicMock()

            # Create mock response with indexed data
            mock_data = [
                MagicMock(index=0, embedding=[0.1]),
                MagicMock(index=1, embedding=[0.2]),
                MagicMock(index=2, embedding=[0.3]),
            ]
            mock_response = MagicMock()
            mock_response.data = mock_data
            mock_client.embeddings.create.return_value = mock_response

            service.client = mock_client
            service.model = "text-embedding-3-small"

            result = service.get_embeddings_batch(["text1", "text2", "text3"])

            assert result == [[0.1], [0.2], [0.3]]


class TestGenerateOpportunityEmbedding:
    """Test generate_opportunity_embedding method."""

    def test_generate_opportunity_embedding_success(self):
        """Test successful opportunity embedding generation."""
        from src.opportunity_radar.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, "__init__", lambda self: None):
            service = EmbeddingService()
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.data = [MagicMock(embedding=[0.1, 0.2])]
            mock_client.embeddings.create.return_value = mock_response

            service.client = mock_client
            service.model = "text-embedding-3-small"

            result = service.generate_opportunity_embedding(
                opportunity_id="opp123",
                title="AI Hackathon",
                description="Build AI apps",
            )

            assert result.success is True
            assert result.id == "opp123"
            assert result.embedding == [0.1, 0.2]
            assert result.text_length > 0

    def test_generate_opportunity_embedding_error(self):
        """Test opportunity embedding generation handles errors."""
        from src.opportunity_radar.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, "__init__", lambda self: None):
            service = EmbeddingService()
            mock_client = MagicMock()
            mock_client.embeddings.create.side_effect = Exception("API error")

            service.client = mock_client
            service.model = "text-embedding-3-small"

            result = service.generate_opportunity_embedding(
                opportunity_id="opp123",
                title="Test",
            )

            assert result.success is False
            assert result.error is not None
            assert result.embedding == []


class TestGenerateOpportunityEmbeddingsBatch:
    """Test generate_opportunity_embeddings_batch method."""

    def test_batch_empty_list(self):
        """Test batch with empty opportunity list."""
        from src.opportunity_radar.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, "__init__", lambda self: None):
            service = EmbeddingService()
            service.client = MagicMock()
            service.model = "text-embedding-3-small"

            results, stats = service.generate_opportunity_embeddings_batch([])

            assert results == []
            assert stats["total"] == 0

    def test_batch_skips_missing_id(self):
        """Test batch skips opportunities without ID."""
        from src.opportunity_radar.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, "__init__", lambda self: None):
            service = EmbeddingService()
            service.client = MagicMock()
            service.model = "text-embedding-3-small"

            opportunities = [{"title": "No ID"}]
            results, stats = service.generate_opportunity_embeddings_batch(opportunities)

            assert stats["skipped"] == 1

    def test_batch_skips_missing_title(self):
        """Test batch skips opportunities without title."""
        from src.opportunity_radar.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, "__init__", lambda self: None):
            service = EmbeddingService()
            service.client = MagicMock()
            service.model = "text-embedding-3-small"

            opportunities = [{"id": "123"}]
            results, stats = service.generate_opportunity_embeddings_batch(opportunities)

            assert len(results) == 1
            assert results[0].success is False

    def test_batch_success(self):
        """Test successful batch embedding generation."""
        from src.opportunity_radar.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, "__init__", lambda self: None):
            service = EmbeddingService()
            mock_client = MagicMock()

            mock_data = [
                MagicMock(index=0, embedding=[0.1]),
                MagicMock(index=1, embedding=[0.2]),
            ]
            mock_response = MagicMock()
            mock_response.data = mock_data
            mock_client.embeddings.create.return_value = mock_response

            service.client = mock_client
            service.model = "text-embedding-3-small"

            opportunities = [
                {"id": "1", "title": "Hackathon 1"},
                {"id": "2", "title": "Hackathon 2"},
            ]
            results, stats = service.generate_opportunity_embeddings_batch(opportunities)

            assert stats["success"] == 2
            assert len(results) == 2


class TestSingleton:
    """Test singleton instance."""

    def test_get_embedding_service(self):
        """Test get_embedding_service returns singleton."""
        from src.opportunity_radar.services.embedding_service import get_embedding_service

        # Reset singleton for test
        import src.opportunity_radar.services.embedding_service as module
        module._embedding_service = None

        with patch.object(module.EmbeddingService, "__init__", lambda self: None):
            service1 = get_embedding_service()
            service2 = get_embedding_service()

            assert service1 is service2
