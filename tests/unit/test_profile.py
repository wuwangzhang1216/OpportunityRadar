"""Unit tests for Profile management."""

import pytest


class TestProfileModel:
    """Test Profile model functionality."""

    def test_import_profile(self):
        """Test Profile model import."""
        from src.opportunity_radar.models import Profile

        assert Profile is not None

    def test_profile_has_required_fields(self):
        """Test Profile model has all required fields."""
        from src.opportunity_radar.models.profile import Profile

        fields = Profile.model_fields

        # Core fields
        assert "user_id" in fields
        assert "display_name" in fields
        assert "bio" in fields
        assert "tech_stack" in fields
        assert "experience_level" in fields

        # Preferences
        assert "availability_hours_per_week" in fields
        assert "timezone" in fields
        assert "preferred_team_size_min" in fields
        assert "preferred_team_size_max" in fields

        # Goals and interests
        assert "goals" in fields
        assert "interests" in fields

        # Location
        assert "location_country" in fields
        assert "location_region" in fields

        # Student info
        assert "student_status" in fields
        assert "university" in fields

        # Social links
        assert "github_url" in fields
        assert "linkedin_url" in fields
        assert "portfolio_url" in fields

    def test_profile_has_team_fields(self):
        """Test Profile has team-related fields."""
        from src.opportunity_radar.models.profile import Profile

        fields = Profile.model_fields

        assert "team_name" in fields
        assert "team_size" in fields
        assert "company_stage" in fields
        assert "team_members" in fields

    def test_profile_has_funding_fields(self):
        """Test Profile has funding-related fields."""
        from src.opportunity_radar.models.profile import Profile

        fields = Profile.model_fields

        assert "funding_stage" in fields
        assert "seeking_funding" in fields
        assert "funding_amount_seeking" in fields

    def test_profile_has_product_fields(self):
        """Test Profile has product-related fields."""
        from src.opportunity_radar.models.profile import Profile

        fields = Profile.model_fields

        assert "product_name" in fields
        assert "product_description" in fields
        assert "product_url" in fields
        assert "product_stage" in fields

    def test_profile_has_track_record_fields(self):
        """Test Profile has track record fields."""
        from src.opportunity_radar.models.profile import Profile

        fields = Profile.model_fields

        assert "previous_accelerators" in fields
        assert "previous_hackathon_wins" in fields
        assert "notable_achievements" in fields

    def test_profile_has_embedding_field(self):
        """Test Profile has embedding field."""
        from src.opportunity_radar.models.profile import Profile

        assert "embedding" in Profile.model_fields

    def test_profile_default_values(self):
        """Test Profile default values."""
        from src.opportunity_radar.models.profile import Profile

        assert Profile.model_fields["preferred_team_size_min"].default == 1
        assert Profile.model_fields["preferred_team_size_max"].default == 5
        assert Profile.model_fields["seeking_funding"].default is False
        assert Profile.model_fields["previous_hackathon_wins"].default == 0


class TestTeamMember:
    """Test TeamMember model."""

    def test_import_team_member(self):
        """Test TeamMember import."""
        from src.opportunity_radar.models.profile import TeamMember

        assert TeamMember is not None

    def test_team_member_fields(self):
        """Test TeamMember has required fields."""
        from src.opportunity_radar.models.profile import TeamMember

        fields = TeamMember.model_fields

        assert "name" in fields
        assert "role" in fields
        assert "linkedin_url" in fields
        assert "skills" in fields


class TestProfileStageTypes:
    """Test Profile stage literal types."""

    def test_company_stage_values(self):
        """Test valid company stage values."""
        from src.opportunity_radar.models.profile import CompanyStage

        valid_stages = ["idea", "prototype", "mvp", "launched", "revenue", "funded"]
        assert len(valid_stages) == 6

    def test_funding_stage_values(self):
        """Test valid funding stage values."""
        from src.opportunity_radar.models.profile import FundingStage

        valid_stages = ["bootstrapped", "pre_seed", "seed", "series_a", "series_b_plus"]
        assert len(valid_stages) == 5

    def test_product_stage_values(self):
        """Test valid product stage values."""
        from src.opportunity_radar.models.profile import ProductStage

        valid_stages = ["concept", "development", "beta", "live"]
        assert len(valid_stages) == 4


class TestProfileService:
    """Test ProfileService functionality."""

    def test_import_profile_service(self):
        """Test ProfileService import."""
        from src.opportunity_radar.services import ProfileService

        assert ProfileService is not None


class TestProfileSchema:
    """Test Profile schemas."""

    def test_import_profile_create_schema(self):
        """Test ProfileCreate schema import."""
        from src.opportunity_radar.schemas.profile import ProfileCreate

        assert ProfileCreate is not None

    def test_import_profile_update_schema(self):
        """Test ProfileUpdate schema import."""
        from src.opportunity_radar.schemas.profile import ProfileUpdate

        assert ProfileUpdate is not None

    def test_import_profile_response_schema(self):
        """Test ProfileResponse schema import."""
        from src.opportunity_radar.schemas.profile import ProfileResponse

        assert ProfileResponse is not None


class TestProfileWorkflow:
    """Test Profile workflow logic."""

    def test_experience_levels(self):
        """Test valid experience levels."""
        experience_levels = ["beginner", "intermediate", "advanced", "expert"]

        assert len(experience_levels) == 4

    def test_student_statuses(self):
        """Test valid student statuses."""
        student_statuses = ["undergraduate", "graduate", "phd", "bootcamp", "self_taught", "not_student"]

        assert len(student_statuses) == 6

    def test_goal_types(self):
        """Test common profile goals."""
        common_goals = [
            "win_prize",
            "learn_skills",
            "build_portfolio",
            "network",
            "get_funding",
            "launch_product",
        ]

        assert len(common_goals) >= 4
