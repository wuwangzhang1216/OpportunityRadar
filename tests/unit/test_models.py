"""Unit tests for models."""

import pytest


class TestModelImports:
    """Test that all models can be imported correctly."""

    def test_import_user(self):
        """Test User model import."""
        from src.opportunity_radar.models import User

        assert User is not None

    def test_import_profile(self):
        """Test Profile model import."""
        from src.opportunity_radar.models import Profile

        assert Profile is not None

    def test_import_opportunity(self):
        """Test Opportunity model import."""
        from src.opportunity_radar.models import Opportunity

        assert Opportunity is not None

    def test_import_host(self):
        """Test Host model import."""
        from src.opportunity_radar.models import Host

        assert Host is not None

    def test_import_match(self):
        """Test Match model import."""
        from src.opportunity_radar.models import Match

        assert Match is not None

    def test_import_pipeline(self):
        """Test Pipeline model import."""
        from src.opportunity_radar.models import Pipeline

        assert Pipeline is not None

    def test_import_material(self):
        """Test Material model import."""
        from src.opportunity_radar.models import Material

        assert Material is not None

    def test_import_scraper_run(self):
        """Test ScraperRun model import."""
        from src.opportunity_radar.models import ScraperRun

        assert ScraperRun is not None


class TestOpportunityModel:
    """Test Opportunity model functionality."""

    def test_opportunity_type_default(self):
        """Test default opportunity type."""
        from src.opportunity_radar.models.opportunity import Opportunity

        # Check class has expected fields
        assert hasattr(Opportunity, "model_fields")
        assert "opportunity_type" in Opportunity.model_fields

    def test_opportunity_has_embedding_field(self):
        """Test that Opportunity has embedding field."""
        from src.opportunity_radar.models.opportunity import Opportunity

        assert "embedding" in Opportunity.model_fields
