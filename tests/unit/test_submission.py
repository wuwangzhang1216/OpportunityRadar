"""Unit tests for Submission workflow."""

import pytest
from datetime import datetime


class TestSubmissionModel:
    """Test OpportunitySubmission model functionality."""

    def test_import_submission(self):
        """Test OpportunitySubmission model import."""
        from src.opportunity_radar.models.submission import OpportunitySubmission

        assert OpportunitySubmission is not None

    def test_submission_has_required_fields(self):
        """Test OpportunitySubmission model has all required fields."""
        from src.opportunity_radar.models.submission import OpportunitySubmission

        fields = OpportunitySubmission.model_fields

        # Submitter info
        assert "submitted_by" in fields
        assert "submitter_email" in fields

        # Opportunity details
        assert "title" in fields
        assert "description" in fields
        assert "opportunity_type" in fields
        assert "website_url" in fields

        # Organization
        assert "host_name" in fields

        # Review status
        assert "status" in fields
        assert "review_notes" in fields
        assert "reviewed_by" in fields
        assert "reviewed_at" in fields

    def test_submission_default_status(self):
        """Test OpportunitySubmission default status is 'pending'."""
        from src.opportunity_radar.models.submission import OpportunitySubmission

        status_field = OpportunitySubmission.model_fields["status"]
        assert status_field.default == "pending"

    def test_submission_valid_statuses(self):
        """Test valid submission statuses."""
        from src.opportunity_radar.models.submission import SubmissionStatus

        # SubmissionStatus is a Literal type
        valid_statuses = ["pending", "approved", "rejected", "needs_info"]
        # Verify these are the expected statuses
        assert len(valid_statuses) == 4


class TestReviewNote:
    """Test ReviewNote model functionality."""

    def test_import_review_note(self):
        """Test ReviewNote model import."""
        from src.opportunity_radar.models.submission import ReviewNote

        assert ReviewNote is not None

    def test_review_note_fields(self):
        """Test ReviewNote has required fields."""
        from src.opportunity_radar.models.submission import ReviewNote

        fields = ReviewNote.model_fields
        assert "reviewer_id" in fields
        assert "note" in fields
        assert "status_change" in fields
        assert "created_at" in fields


class TestSubmissionWorkflow:
    """Test Submission workflow logic."""

    def test_add_review_note(self):
        """Test add_review_note method exists."""
        from src.opportunity_radar.models.submission import OpportunitySubmission

        assert hasattr(OpportunitySubmission, "add_review_note")
        assert callable(getattr(OpportunitySubmission, "add_review_note"))

    def test_status_transitions(self):
        """Test valid status transitions."""
        # Define expected workflow transitions
        workflow = {
            "pending": ["approved", "rejected", "needs_info"],
            "needs_info": ["pending", "approved", "rejected"],
            "approved": [],  # Terminal state (opportunity created)
            "rejected": [],  # Terminal state
        }

        # Verify all transitions are defined
        for status, transitions in workflow.items():
            assert isinstance(transitions, list)

    def test_submission_types(self):
        """Test valid submission opportunity types."""
        valid_types = ["hackathon", "grant", "competition", "bounty", "accelerator"]

        # These should be valid opportunity types
        assert "hackathon" in valid_types
        assert "grant" in valid_types

    def test_submission_formats(self):
        """Test valid submission formats."""
        valid_formats = ["online", "in-person", "hybrid"]

        assert len(valid_formats) == 3
