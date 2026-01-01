"""API v1 router aggregation."""

from fastapi import APIRouter

from .endpoints import auth, opportunities, profiles, matches, materials, pipelines, onboarding

api_router = APIRouter(prefix="/v1")

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["Onboarding"])
api_router.include_router(opportunities.router, prefix="/opportunities", tags=["Opportunities"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["Profiles"])
api_router.include_router(matches.router, prefix="/matches", tags=["Matches"])
api_router.include_router(materials.router, prefix="/materials", tags=["Materials"])
api_router.include_router(pipelines.router, prefix="/pipelines", tags=["Pipelines"])
