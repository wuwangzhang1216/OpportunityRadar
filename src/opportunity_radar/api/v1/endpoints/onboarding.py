"""Onboarding API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from ....core.security import get_current_user
from ....models.user import User
from ....schemas.onboarding import (
    OnboardingConfirmRequest,
    OnboardingConfirmResponse,
    OnboardingStatusResponse,
    URLExtractRequest,
    URLExtractResponse,
    COMMON_TECH_STACKS,
    COMMON_GOALS,
    COMMON_INDUSTRIES,
)
from ....services.onboarding_service import get_onboarding_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/extract", response_model=URLExtractResponse)
async def extract_profile_from_url(
    request: URLExtractRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Extract profile information from a URL.

    Supports:
    - Company/product websites
    - GitHub repositories

    Returns extracted fields with confidence scores.
    """
    service = get_onboarding_service()

    try:
        extracted_profile = await service.extract_profile_from_url(request.url)

        return URLExtractResponse(
            success=True,
            extracted_profile=extracted_profile,
        )

    except Exception as e:
        logger.error(f"URL extraction failed for {request.url}: {e}")
        return URLExtractResponse(
            success=False,
            error_message=f"Failed to extract profile from URL: {str(e)}",
        )


@router.post("/confirm", response_model=OnboardingConfirmResponse)
async def confirm_profile(
    request: OnboardingConfirmRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Confirm extracted profile data and create/update user profile.

    This finalizes the onboarding process and creates the user's profile
    with the confirmed data.
    """
    service = get_onboarding_service()

    try:
        profile = await service.confirm_profile(current_user, request)

        return OnboardingConfirmResponse(
            success=True,
            profile_id=str(profile.id),
            onboarding_completed=True,
        )

    except Exception as e:
        logger.error(f"Profile confirmation failed for user {current_user.id}: {e}")
        return OnboardingConfirmResponse(
            success=False,
            error_message=f"Failed to create profile: {str(e)}",
        )


@router.get("/status", response_model=OnboardingStatusResponse)
async def get_onboarding_status(
    current_user: User = Depends(get_current_user),
):
    """
    Check if user has completed onboarding.

    Returns whether the user has a profile and has completed onboarding.
    """
    service = get_onboarding_service()
    status_data = await service.get_onboarding_status(current_user)

    return OnboardingStatusResponse(**status_data)


@router.get("/suggestions")
async def get_onboarding_suggestions(
    current_user: User = Depends(get_current_user),
):
    """
    Get suggestion lists for onboarding form fields.

    Returns common options for tech stacks, goals, and industries.
    """
    return {
        "tech_stacks": COMMON_TECH_STACKS,
        "goals": COMMON_GOALS,
        "industries": COMMON_INDUSTRIES,
    }
