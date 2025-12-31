"""Profile API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from ....models.profile import Profile
from ....models.user import User
from ....core.security import get_current_user

router = APIRouter()


@router.get("/me")
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile."""
    profile = await Profile.find_one(Profile.user_id == current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    return profile


@router.post("")
async def create_profile(
    profile_data: dict,
    current_user: User = Depends(get_current_user),
):
    """Create user profile."""
    existing = await Profile.find_one(Profile.user_id == current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile already exists",
        )

    profile = Profile(user_id=current_user.id, **profile_data)
    await profile.insert()
    return profile


@router.put("/me")
async def update_profile(
    profile_data: dict,
    current_user: User = Depends(get_current_user),
):
    """Update current user's profile."""
    profile = await Profile.find_one(Profile.user_id == current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    for key, value in profile_data.items():
        if hasattr(profile, key):
            setattr(profile, key, value)

    await profile.save()
    return profile
