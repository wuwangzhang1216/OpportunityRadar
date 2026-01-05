"""Profile API endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from ....models.profile import Profile, TeamMember
from ....models.user import User
from ....core.security import get_current_user
from ....schemas.profile import ProfileCreate, ProfileUpdate, ProfileResponse

router = APIRouter()


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile."""
    profile = await Profile.find_one(Profile.user_id == current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    return ProfileResponse(
        id=str(profile.id),
        user_id=str(profile.user_id),
        profile_type=profile.experience_level,
        stage=profile.company_stage,
        tech_stack=profile.tech_stack,
        industries=profile.interests,
        team_size=profile.team_size or 1,
        availability=[],
        wins=profile.notable_achievements,
        intents=profile.goals,
        team_name=profile.team_name,
        company_stage=profile.company_stage,
        funding_stage=profile.funding_stage,
        seeking_funding=profile.seeking_funding,
        funding_amount_seeking=profile.funding_amount_seeking,
        product_name=profile.product_name,
        product_description=profile.product_description,
        product_url=profile.product_url,
        product_stage=profile.product_stage,
        team_members=[
            {"name": tm.name, "role": tm.role, "linkedin_url": tm.linkedin_url, "skills": tm.skills}
            for tm in profile.team_members
        ],
        previous_accelerators=profile.previous_accelerators,
        previous_hackathon_wins=profile.previous_hackathon_wins,
        notable_achievements=profile.notable_achievements,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile_data: ProfileCreate,
    current_user: User = Depends(get_current_user),
):
    """Create user profile."""
    existing = await Profile.find_one(Profile.user_id == current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile already exists",
        )

    # Convert team members
    team_members = [
        TeamMember(**tm.model_dump()) for tm in profile_data.team_members
    ] if profile_data.team_members else []

    profile = Profile(
        user_id=current_user.id,
        tech_stack=profile_data.tech_stack,
        interests=profile_data.industries,
        goals=profile_data.intents,
        team_name=profile_data.team_name,
        team_size=profile_data.team_size,
        company_stage=profile_data.company_stage,
        funding_stage=profile_data.funding_stage,
        seeking_funding=profile_data.seeking_funding,
        funding_amount_seeking=profile_data.funding_amount_seeking,
        product_name=profile_data.product_name,
        product_description=profile_data.product_description,
        product_url=profile_data.product_url,
        product_stage=profile_data.product_stage,
        team_members=team_members,
        previous_accelerators=profile_data.previous_accelerators,
        previous_hackathon_wins=profile_data.previous_hackathon_wins,
        notable_achievements=profile_data.notable_achievements,
    )
    await profile.insert()

    return ProfileResponse(
        id=str(profile.id),
        user_id=str(profile.user_id),
        profile_type=profile.experience_level,
        stage=profile.company_stage,
        tech_stack=profile.tech_stack,
        industries=profile.interests,
        team_size=profile.team_size or 1,
        availability=[],
        wins=profile.notable_achievements,
        intents=profile.goals,
        team_name=profile.team_name,
        company_stage=profile.company_stage,
        funding_stage=profile.funding_stage,
        seeking_funding=profile.seeking_funding,
        funding_amount_seeking=profile.funding_amount_seeking,
        product_name=profile.product_name,
        product_description=profile.product_description,
        product_url=profile.product_url,
        product_stage=profile.product_stage,
        team_members=[
            {"name": tm.name, "role": tm.role, "linkedin_url": tm.linkedin_url, "skills": tm.skills}
            for tm in profile.team_members
        ],
        previous_accelerators=profile.previous_accelerators,
        previous_hackathon_wins=profile.previous_hackathon_wins,
        notable_achievements=profile.notable_achievements,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.put("/me", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update current user's profile."""
    profile = await Profile.find_one(Profile.user_id == current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    # Update only provided fields
    update_data = profile_data.model_dump(exclude_unset=True)

    # Handle team members specially
    if "team_members" in update_data and update_data["team_members"] is not None:
        update_data["team_members"] = [
            TeamMember(**tm) for tm in update_data["team_members"]
        ]

    # Map schema fields to model fields
    field_mapping = {
        "industries": "interests",
        "intents": "goals",
        "wins": "notable_achievements",
    }

    for schema_field, model_field in field_mapping.items():
        if schema_field in update_data:
            update_data[model_field] = update_data.pop(schema_field)

    for key, value in update_data.items():
        if hasattr(profile, key) and value is not None:
            setattr(profile, key, value)

    profile.updated_at = datetime.utcnow()
    await profile.save()

    return ProfileResponse(
        id=str(profile.id),
        user_id=str(profile.user_id),
        profile_type=profile.experience_level,
        stage=profile.company_stage,
        tech_stack=profile.tech_stack,
        industries=profile.interests,
        team_size=profile.team_size or 1,
        availability=[],
        wins=profile.notable_achievements,
        intents=profile.goals,
        team_name=profile.team_name,
        company_stage=profile.company_stage,
        funding_stage=profile.funding_stage,
        seeking_funding=profile.seeking_funding,
        funding_amount_seeking=profile.funding_amount_seeking,
        product_name=profile.product_name,
        product_description=profile.product_description,
        product_url=profile.product_url,
        product_stage=profile.product_stage,
        team_members=[
            {"name": tm.name, "role": tm.role, "linkedin_url": tm.linkedin_url, "skills": tm.skills}
            for tm in profile.team_members
        ],
        previous_accelerators=profile.previous_accelerators,
        previous_hackathon_wins=profile.previous_hackathon_wins,
        notable_achievements=profile.notable_achievements,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )
