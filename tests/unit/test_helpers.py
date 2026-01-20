"""Unit tests for API endpoint helpers."""

import pytest


class TestHelpersImport:
    """Test helpers module imports."""

    def test_import_get_user_document(self):
        """Test get_user_document import."""
        from src.opportunity_radar.api.v1.endpoints.helpers import get_user_document

        assert get_user_document is not None
        assert callable(get_user_document)

    def test_import_get_user_match(self):
        """Test get_user_match import."""
        from src.opportunity_radar.api.v1.endpoints.helpers import get_user_match

        assert get_user_match is not None
        assert callable(get_user_match)

    def test_import_enrich_match_with_opportunity(self):
        """Test enrich_match_with_opportunity import."""
        from src.opportunity_radar.api.v1.endpoints.helpers import (
            enrich_match_with_opportunity,
        )

        assert enrich_match_with_opportunity is not None
        assert callable(enrich_match_with_opportunity)

    def test_import_enrich_matches_with_opportunities(self):
        """Test enrich_matches_with_opportunities import."""
        from src.opportunity_radar.api.v1.endpoints.helpers import (
            enrich_matches_with_opportunities,
        )

        assert enrich_matches_with_opportunities is not None
        assert callable(enrich_matches_with_opportunities)

    def test_import_fetch_opportunities_by_ids(self):
        """Test fetch_opportunities_by_ids import."""
        from src.opportunity_radar.api.v1.endpoints.helpers import (
            fetch_opportunities_by_ids,
        )

        assert fetch_opportunities_by_ids is not None
        assert callable(fetch_opportunities_by_ids)


class TestHelpersAsync:
    """Test that helper functions are async."""

    def test_get_user_document_is_async(self):
        """Test get_user_document is async."""
        import asyncio
        from src.opportunity_radar.api.v1.endpoints.helpers import get_user_document

        assert asyncio.iscoroutinefunction(get_user_document)

    def test_get_user_match_is_async(self):
        """Test get_user_match is async."""
        import asyncio
        from src.opportunity_radar.api.v1.endpoints.helpers import get_user_match

        assert asyncio.iscoroutinefunction(get_user_match)

    def test_enrich_matches_is_async(self):
        """Test enrich_matches_with_opportunities is async."""
        import asyncio
        from src.opportunity_radar.api.v1.endpoints.helpers import (
            enrich_matches_with_opportunities,
        )

        assert asyncio.iscoroutinefunction(enrich_matches_with_opportunities)

    def test_fetch_opportunities_is_async(self):
        """Test fetch_opportunities_by_ids is async."""
        import asyncio
        from src.opportunity_radar.api.v1.endpoints.helpers import (
            fetch_opportunities_by_ids,
        )

        assert asyncio.iscoroutinefunction(fetch_opportunities_by_ids)


class TestEnrichMatchWithOpportunity:
    """Test enrich_match_with_opportunity function."""

    def test_enrich_with_none_opportunity(self):
        """Test enriching match when opportunity is None."""
        from unittest.mock import MagicMock
        from src.opportunity_radar.api.v1.endpoints.helpers import (
            enrich_match_with_opportunity,
        )

        # Create a mock match
        mock_match = MagicMock()
        mock_match.model_dump.return_value = {"id": "match_123"}
        mock_match.overall_score = 0.85
        mock_match.opportunity_id = "opp_456"

        result = enrich_match_with_opportunity(mock_match, None)

        assert result["score"] == 0.85
        assert result["batch_id"] == "opp_456"
        assert result["opportunity_title"] is None
        assert result["opportunity_category"] is None
        assert result["deadline"] is None
        assert result["opportunity_url"] is None

    def test_enrich_includes_description_when_requested(self):
        """Test enriching includes description when flag is set."""
        from unittest.mock import MagicMock
        from src.opportunity_radar.api.v1.endpoints.helpers import (
            enrich_match_with_opportunity,
        )

        mock_match = MagicMock()
        mock_match.model_dump.return_value = {}
        mock_match.overall_score = 0.5
        mock_match.opportunity_id = None

        mock_opp = MagicMock()
        mock_opp.title = "Test Opportunity"
        mock_opp.opportunity_type = "hackathon"
        mock_opp.description = "A detailed description"
        mock_opp.application_deadline = None
        mock_opp.website_url = "https://example.com"
        mock_opp.total_prize_value = 10000

        result = enrich_match_with_opportunity(
            mock_match, mock_opp, include_description=True
        )

        assert result["opportunity_description"] == "A detailed description"

    def test_enrich_includes_prize_pool_when_requested(self):
        """Test enriching includes prize pool when flag is set."""
        from unittest.mock import MagicMock
        from src.opportunity_radar.api.v1.endpoints.helpers import (
            enrich_match_with_opportunity,
        )

        mock_match = MagicMock()
        mock_match.model_dump.return_value = {}
        mock_match.overall_score = 0.5
        mock_match.opportunity_id = None

        mock_opp = MagicMock()
        mock_opp.title = "Test"
        mock_opp.opportunity_type = "hackathon"
        mock_opp.application_deadline = None
        mock_opp.website_url = None
        mock_opp.total_prize_value = 50000

        result = enrich_match_with_opportunity(
            mock_match, mock_opp, include_prize_pool=True
        )

        assert result["opportunity_prize_pool"] == 50000

    def test_enrich_excludes_optional_fields_by_default(self):
        """Test enriching excludes optional fields by default."""
        from unittest.mock import MagicMock
        from src.opportunity_radar.api.v1.endpoints.helpers import (
            enrich_match_with_opportunity,
        )

        mock_match = MagicMock()
        mock_match.model_dump.return_value = {}
        mock_match.overall_score = 0.5
        mock_match.opportunity_id = None

        mock_opp = MagicMock()
        mock_opp.title = "Test"
        mock_opp.opportunity_type = "hackathon"
        mock_opp.description = "Description"
        mock_opp.application_deadline = None
        mock_opp.website_url = None
        mock_opp.total_prize_value = 10000

        result = enrich_match_with_opportunity(mock_match, mock_opp)

        assert "opportunity_description" not in result
        assert "opportunity_prize_pool" not in result
