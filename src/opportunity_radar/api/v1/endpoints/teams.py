"""Team collaboration API endpoints."""

from datetime import datetime, timedelta
from typing import List, Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from ....models.team import Team, TeamMemberInfo, TeamInvite
from ....models.user import User
from ....models.opportunity import Opportunity
from ....core.security import get_current_user

router = APIRouter()


class TeamCreate(BaseModel):
    """Schema for creating a team."""

    name: str
    description: Optional[str] = None


class TeamUpdate(BaseModel):
    """Schema for updating a team."""

    name: Optional[str] = None
    description: Optional[str] = None


class TeamMemberResponse(BaseModel):
    """Team member response."""

    user_id: str
    email: str
    full_name: Optional[str]
    role: str
    joined_at: str


class TeamResponse(BaseModel):
    """Team response schema."""

    id: str
    name: str
    description: Optional[str]
    owner_id: str
    member_count: int
    created_at: str


class TeamDetailResponse(TeamResponse):
    """Detailed team response with members."""

    members: List[TeamMemberResponse]
    shared_opportunity_count: int


class InviteMemberRequest(BaseModel):
    """Request to invite a member."""

    email: EmailStr


class ShareOpportunityRequest(BaseModel):
    """Request to share an opportunity."""

    opportunity_id: str


@router.get("", response_model=List[TeamResponse])
async def list_my_teams(
    current_user: User = Depends(get_current_user),
):
    """List teams the current user belongs to."""
    teams = await Team.find(
        {"members.user_id": current_user.id}
    ).to_list()

    return [
        TeamResponse(
            id=str(team.id),
            name=team.name,
            description=team.description,
            owner_id=str(team.owner_id),
            member_count=len(team.members),
            created_at=team.created_at.isoformat(),
        )
        for team in teams
    ]


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a new team."""
    team = Team(
        name=team_data.name,
        description=team_data.description,
        owner_id=current_user.id,
    )

    # Add owner as first member
    team.add_member(current_user.id, role="owner")

    await team.insert()

    return TeamResponse(
        id=str(team.id),
        name=team.name,
        description=team.description,
        owner_id=str(team.owner_id),
        member_count=len(team.members),
        created_at=team.created_at.isoformat(),
    )


@router.get("/{team_id}", response_model=TeamDetailResponse)
async def get_team(
    team_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get team details."""
    team = await Team.get(PydanticObjectId(team_id))

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    if not team.is_member(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team",
        )

    # Get member details
    members = []
    for member_info in team.members:
        user = await User.get(member_info.user_id)
        if user:
            members.append(
                TeamMemberResponse(
                    user_id=str(member_info.user_id),
                    email=user.email,
                    full_name=user.full_name,
                    role=member_info.role,
                    joined_at=member_info.joined_at.isoformat(),
                )
            )

    return TeamDetailResponse(
        id=str(team.id),
        name=team.name,
        description=team.description,
        owner_id=str(team.owner_id),
        member_count=len(team.members),
        created_at=team.created_at.isoformat(),
        members=members,
        shared_opportunity_count=len(team.shared_opportunities),
    )


@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: str,
    team_data: TeamUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update team details (admin only)."""
    team = await Team.get(PydanticObjectId(team_id))

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    if not team.is_admin(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update team details",
        )

    if team_data.name:
        team.name = team_data.name
    if team_data.description is not None:
        team.description = team_data.description

    team.updated_at = datetime.utcnow()
    await team.save()

    return TeamResponse(
        id=str(team.id),
        name=team.name,
        description=team.description,
        owner_id=str(team.owner_id),
        member_count=len(team.members),
        created_at=team.created_at.isoformat(),
    )


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a team (owner only)."""
    team = await Team.get(PydanticObjectId(team_id))

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    if team.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can delete the team",
        )

    await team.delete()


@router.post("/{team_id}/invite")
async def invite_member(
    team_id: str,
    invite: InviteMemberRequest,
    current_user: User = Depends(get_current_user),
):
    """Invite a user to the team."""
    team = await Team.get(PydanticObjectId(team_id))

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    if not team.is_admin(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can invite members",
        )

    # Check if already invited or member
    invited_user = await User.find_one(User.email == invite.email)
    if invited_user and team.is_member(invited_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member",
        )

    # Check for existing pending invite
    for existing_invite in team.invites:
        if existing_invite.email == invite.email and existing_invite.status == "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation already pending",
            )

    # Create invite
    team.invites.append(
        TeamInvite(
            email=invite.email,
            invited_by=current_user.id,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
    )
    team.updated_at = datetime.utcnow()
    await team.save()

    return {"message": f"Invitation sent to {invite.email}"}


@router.post("/{team_id}/join")
async def join_team(
    team_id: str,
    current_user: User = Depends(get_current_user),
):
    """Accept a team invitation."""
    team = await Team.get(PydanticObjectId(team_id))

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    if team.is_member(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already a member",
        )

    # Find pending invite
    invite = None
    for inv in team.invites:
        if inv.email == current_user.email and inv.status == "pending":
            invite = inv
            break

    if not invite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending invitation found",
        )

    # Check expiry
    if invite.expires_at and invite.expires_at < datetime.utcnow():
        invite.status = "expired"
        await team.save()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has expired",
        )

    # Accept invite and add member
    invite.status = "accepted"
    team.add_member(current_user.id, role="member")
    await team.save()

    return {"message": "Joined team successfully"}


@router.delete("/{team_id}/leave")
async def leave_team(
    team_id: str,
    current_user: User = Depends(get_current_user),
):
    """Leave a team."""
    team = await Team.get(PydanticObjectId(team_id))

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    if not team.is_member(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not a member of this team",
        )

    if team.owner_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner cannot leave. Transfer ownership or delete the team.",
        )

    team.remove_member(current_user.id)
    await team.save()

    return {"message": "Left team successfully"}


@router.post("/{team_id}/share")
async def share_opportunity(
    team_id: str,
    share: ShareOpportunityRequest,
    current_user: User = Depends(get_current_user),
):
    """Share an opportunity with the team."""
    team = await Team.get(PydanticObjectId(team_id))

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    if not team.is_member(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team",
        )

    # Verify opportunity exists
    opp_id = PydanticObjectId(share.opportunity_id)
    opp = await Opportunity.get(opp_id)
    if not opp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found",
        )

    team.share_opportunity(opp_id)
    await team.save()

    return {"message": "Opportunity shared with team"}


@router.get("/{team_id}/opportunities")
async def get_team_opportunities(
    team_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get opportunities shared with the team."""
    team = await Team.get(PydanticObjectId(team_id))

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    if not team.is_member(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team",
        )

    opportunities = []
    for opp_id in team.shared_opportunities:
        opp = await Opportunity.get(opp_id)
        if opp:
            opportunities.append({
                "id": str(opp.id),
                "title": opp.title,
                "type": opp.opportunity_type,
                "logo_url": opp.logo_url,
                "website_url": opp.website_url,
            })

    return {"opportunities": opportunities}
