"""API v1 router aggregation."""

from fastapi import APIRouter

from .endpoints import auth, opportunities, profiles, matches, materials, pipelines, onboarding, notifications, teams, submissions, calendar, export, community
from .admin import admin_router

api_router = APIRouter(prefix="/v1")

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["Onboarding"])
api_router.include_router(opportunities.router, prefix="/opportunities", tags=["Opportunities"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["Profiles"])
api_router.include_router(matches.router, prefix="/matches", tags=["Matches"])
api_router.include_router(materials.router, prefix="/materials", tags=["Materials"])
api_router.include_router(pipelines.router, prefix="/pipelines", tags=["Pipelines"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(teams.router, prefix="/teams", tags=["Teams"])
api_router.include_router(submissions.router, prefix="/submissions", tags=["Submissions"])
api_router.include_router(calendar.router, prefix="/calendar", tags=["Calendar"])
api_router.include_router(export.router, prefix="/export", tags=["Export"])
api_router.include_router(community.router, prefix="/community", tags=["Community"])

# Admin endpoints
api_router.include_router(admin_router)
