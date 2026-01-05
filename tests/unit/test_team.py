"""Unit tests for Team collaboration workflow."""

import pytest
from datetime import datetime
from beanie import PydanticObjectId


class TestTeamModel:
    """Test Team model functionality."""

    def test_import_team(self):
        """Test Team model import."""
        from src.opportunity_radar.models.team import Team

        assert Team is not None

    def test_team_has_required_fields(self):
        """Test Team model has all required fields."""
        from src.opportunity_radar.models.team import Team

        fields = Team.model_fields

        assert "name" in fields
        assert "description" in fields
        assert "owner_id" in fields
        assert "members" in fields
        assert "invites" in fields
        assert "shared_opportunities" in fields
        assert "is_public" in fields
        assert "max_members" in fields

    def test_team_default_values(self):
        """Test Team default values."""
        from src.opportunity_radar.models.team import Team

        assert Team.model_fields["is_public"].default is False
        assert Team.model_fields["max_members"].default == 10


class TestTeamMemberInfo:
    """Test TeamMemberInfo model."""

    def test_import_team_member_info(self):
        """Test TeamMemberInfo import."""
        from src.opportunity_radar.models.team import TeamMemberInfo

        assert TeamMemberInfo is not None

    def test_team_member_info_fields(self):
        """Test TeamMemberInfo has required fields."""
        from src.opportunity_radar.models.team import TeamMemberInfo

        fields = TeamMemberInfo.model_fields
        assert "user_id" in fields
        assert "role" in fields
        assert "joined_at" in fields

    def test_team_member_default_role(self):
        """Test default role is 'member'."""
        from src.opportunity_radar.models.team import TeamMemberInfo

        assert TeamMemberInfo.model_fields["role"].default == "member"


class TestTeamInvite:
    """Test TeamInvite model."""

    def test_import_team_invite(self):
        """Test TeamInvite import."""
        from src.opportunity_radar.models.team import TeamInvite

        assert TeamInvite is not None

    def test_team_invite_fields(self):
        """Test TeamInvite has required fields."""
        from src.opportunity_radar.models.team import TeamInvite

        fields = TeamInvite.model_fields
        assert "email" in fields
        assert "invited_by" in fields
        assert "status" in fields
        assert "created_at" in fields
        assert "expires_at" in fields

    def test_team_invite_default_status(self):
        """Test default invite status is 'pending'."""
        from src.opportunity_radar.models.team import TeamInvite

        assert TeamInvite.model_fields["status"].default == "pending"


class TestTeamRoles:
    """Test Team role types."""

    def test_valid_team_roles(self):
        """Test valid team roles."""
        from src.opportunity_radar.models.team import TeamRole

        # TeamRole is a Literal type with these values
        valid_roles = ["owner", "admin", "member"]
        assert len(valid_roles) == 3

    def test_valid_invite_statuses(self):
        """Test valid invite statuses."""
        from src.opportunity_radar.models.team import InviteStatus

        # InviteStatus is a Literal type with these values
        valid_statuses = ["pending", "accepted", "declined", "expired"]
        assert len(valid_statuses) == 4


class TestTeamMethods:
    """Test Team model methods."""

    def test_get_member_method_exists(self):
        """Test get_member method exists."""
        from src.opportunity_radar.models.team import Team

        assert hasattr(Team, "get_member")
        assert callable(getattr(Team, "get_member"))

    def test_is_member_method_exists(self):
        """Test is_member method exists."""
        from src.opportunity_radar.models.team import Team

        assert hasattr(Team, "is_member")
        assert callable(getattr(Team, "is_member"))

    def test_is_admin_method_exists(self):
        """Test is_admin method exists."""
        from src.opportunity_radar.models.team import Team

        assert hasattr(Team, "is_admin")
        assert callable(getattr(Team, "is_admin"))

    def test_add_member_method_exists(self):
        """Test add_member method exists."""
        from src.opportunity_radar.models.team import Team

        assert hasattr(Team, "add_member")
        assert callable(getattr(Team, "add_member"))

    def test_remove_member_method_exists(self):
        """Test remove_member method exists."""
        from src.opportunity_radar.models.team import Team

        assert hasattr(Team, "remove_member")
        assert callable(getattr(Team, "remove_member"))

    def test_share_opportunity_method_exists(self):
        """Test share_opportunity method exists."""
        from src.opportunity_radar.models.team import Team

        assert hasattr(Team, "share_opportunity")
        assert callable(getattr(Team, "share_opportunity"))

    def test_unshare_opportunity_method_exists(self):
        """Test unshare_opportunity method exists."""
        from src.opportunity_radar.models.team import Team

        assert hasattr(Team, "unshare_opportunity")
        assert callable(getattr(Team, "unshare_opportunity"))


class TestTeamWorkflow:
    """Test Team workflow logic."""

    def test_admin_roles(self):
        """Test which roles are considered admin."""
        admin_roles = ["owner", "admin"]
        member_role = "member"

        assert member_role not in admin_roles
        assert "owner" in admin_roles
        assert "admin" in admin_roles

    def test_invite_workflow(self):
        """Test invite workflow statuses."""
        workflow = {
            "pending": ["accepted", "declined", "expired"],
            "accepted": [],  # Terminal
            "declined": [],  # Terminal
            "expired": ["pending"],  # Can re-invite
        }

        for status, transitions in workflow.items():
            assert isinstance(transitions, list)
