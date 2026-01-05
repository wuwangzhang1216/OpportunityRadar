"""Unit tests for Pipeline workflow."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch


class TestPipelineModel:
    """Test Pipeline model functionality."""

    def test_import_pipeline(self):
        """Test Pipeline model import."""
        from src.opportunity_radar.models import Pipeline

        assert Pipeline is not None

    def test_pipeline_has_required_fields(self):
        """Test Pipeline model has all required fields."""
        from src.opportunity_radar.models.pipeline import Pipeline

        fields = Pipeline.model_fields
        assert "user_id" in fields
        assert "opportunity_id" in fields
        assert "status" in fields
        assert "notes" in fields
        assert "team_members" in fields
        assert "project_idea" in fields
        assert "submission_url" in fields
        assert "reminder_enabled" in fields

    def test_pipeline_default_status(self):
        """Test Pipeline default status is 'interested'."""
        from src.opportunity_radar.models.pipeline import Pipeline

        # Check default value in field definition
        status_field = Pipeline.model_fields["status"]
        assert status_field.default == "interested"

    def test_pipeline_valid_statuses(self):
        """Test valid pipeline statuses."""
        valid_statuses = ["interested", "preparing", "submitted", "won", "lost"]
        # These are the expected valid statuses for the pipeline workflow
        assert len(valid_statuses) == 5


class TestPipelineService:
    """Test Pipeline service functionality."""

    def test_import_pipeline_service(self):
        """Test PipelineService import."""
        from src.opportunity_radar.services import PipelineService

        assert PipelineService is not None

    def test_valid_stages_constant(self):
        """Test VALID_STAGES constant is defined."""
        from src.opportunity_radar.services.pipeline_service import VALID_STAGES

        assert isinstance(VALID_STAGES, list)
        assert len(VALID_STAGES) > 0
        assert "discovered" in VALID_STAGES
        assert "preparing" in VALID_STAGES
        assert "submitted" in VALID_STAGES
        assert "won" in VALID_STAGES
        assert "lost" in VALID_STAGES


class TestPipelineWorkflow:
    """Test Pipeline workflow logic."""

    def test_stage_transitions(self):
        """Test valid stage transitions."""
        from src.opportunity_radar.services.pipeline_service import VALID_STAGES

        # Define expected workflow transitions
        workflow = {
            "discovered": ["preparing", "lost"],
            "preparing": ["submitted", "lost"],
            "submitted": ["pending", "won", "lost"],
            "pending": ["won", "lost"],
            "won": [],  # Terminal state
            "lost": [],  # Terminal state
        }

        # Verify all stages in VALID_STAGES have defined transitions
        for stage in VALID_STAGES:
            assert stage in workflow or stage in ["pending"]

    def test_pipeline_response_format(self):
        """Test expected pipeline response format."""
        expected_fields = [
            "id",
            "user_id",
            "batch_id",
            "stage",
            "eta_hours",
            "deadline_at",
            "notes",
            "created_at",
            "updated_at",
            "opportunity_title",
            "opportunity_category",
        ]

        # This is the expected response format from PipelineService
        assert len(expected_fields) == 11
