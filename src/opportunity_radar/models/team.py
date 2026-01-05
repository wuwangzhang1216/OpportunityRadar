"""Team model for team collaboration."""

from datetime import datetime
from typing import List, Literal, Optional

from beanie import Document, Indexed, PydanticObjectId
from pydantic import BaseModel, Field


TeamRole = Literal["owner", "admin", "member"]
InviteStatus = Literal["pending", "accepted", "declined", "expired"]


class TeamMemberInfo(BaseModel):
    """Team member information."""

    user_id: PydanticObjectId
    role: TeamRole = "member"
    joined_at: datetime = Field(default_factory=datetime.utcnow)


class TeamInvite(BaseModel):
    """Team invitation."""

    email: str
    invited_by: PydanticObjectId
    status: InviteStatus = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


class Team(Document):
    """Team for collaboration on opportunities."""

    name: str
    description: Optional[str] = None
    owner_id: Indexed(PydanticObjectId)

    # Team members
    members: List[TeamMemberInfo] = Field(default_factory=list)

    # Pending invites
    invites: List[TeamInvite] = Field(default_factory=list)

    # Shared opportunities (bookmarked for the team)
    shared_opportunities: List[PydanticObjectId] = Field(default_factory=list)

    # Team settings
    is_public: bool = False  # Can others discover this team?
    max_members: int = 10

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "teams"
        indexes = [
            "owner_id",
        ]

    def get_member(self, user_id: PydanticObjectId) -> Optional[TeamMemberInfo]:
        """Get member by user ID."""
        for member in self.members:
            if member.user_id == user_id:
                return member
        return None

    def is_member(self, user_id: PydanticObjectId) -> bool:
        """Check if user is a member of the team."""
        return self.get_member(user_id) is not None

    def is_admin(self, user_id: PydanticObjectId) -> bool:
        """Check if user is an admin or owner."""
        member = self.get_member(user_id)
        if not member:
            return False
        return member.role in ["owner", "admin"]

    def add_member(
        self,
        user_id: PydanticObjectId,
        role: TeamRole = "member",
    ) -> None:
        """Add a member to the team."""
        if not self.is_member(user_id):
            self.members.append(
                TeamMemberInfo(user_id=user_id, role=role)
            )
            self.updated_at = datetime.utcnow()

    def remove_member(self, user_id: PydanticObjectId) -> bool:
        """Remove a member from the team."""
        original_count = len(self.members)
        self.members = [m for m in self.members if m.user_id != user_id]
        if len(self.members) < original_count:
            self.updated_at = datetime.utcnow()
            return True
        return False

    def share_opportunity(self, opportunity_id: PydanticObjectId) -> None:
        """Share an opportunity with the team."""
        if opportunity_id not in self.shared_opportunities:
            self.shared_opportunities.append(opportunity_id)
            self.updated_at = datetime.utcnow()

    def unshare_opportunity(self, opportunity_id: PydanticObjectId) -> bool:
        """Unshare an opportunity from the team."""
        if opportunity_id in self.shared_opportunities:
            self.shared_opportunities.remove(opportunity_id)
            self.updated_at = datetime.utcnow()
            return True
        return False
