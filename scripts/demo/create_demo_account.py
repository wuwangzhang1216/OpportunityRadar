"""Create demo account for recording demos."""

import asyncio
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from datetime import datetime, timezone

# Demo Account Credentials
DEMO_EMAIL = "demo@doxmind.com"
DEMO_PASSWORD = "DemoRadar2024!"
DEMO_FULL_NAME = "DoxMind Team"


async def create_demo_account():
    """Create demo account with pre-filled profile."""
    from src.opportunity_radar.db.mongodb import init_db
    from src.opportunity_radar.core.security import get_password_hash
    from src.opportunity_radar.models.user import User
    from src.opportunity_radar.models.profile import Profile

    # Initialize database
    print("Connecting to database...")
    await init_db()
    print("Connected!")

    # Check if demo account exists
    existing_user = await User.find_one(User.email == DEMO_EMAIL)

    if existing_user:
        print(f"Demo account already exists: {DEMO_EMAIL}")
        # Update password to ensure it's correct
        existing_user.hashed_password = get_password_hash(DEMO_PASSWORD)
        existing_user.full_name = DEMO_FULL_NAME
        existing_user.updated_at = datetime.now(timezone.utc)
        await existing_user.save()
        print("Password and name updated!")
        user = existing_user
    else:
        # Create new demo user
        print("Creating new demo account...")
        user = User(
            email=DEMO_EMAIL,
            hashed_password=get_password_hash(DEMO_PASSWORD),
            full_name=DEMO_FULL_NAME,
            is_active=True,
            is_superuser=False,
        )
        await user.insert()
        print(f"Demo account created: {DEMO_EMAIL}")

    # Check/Create profile
    existing_profile = await Profile.find_one(Profile.user_id == user.id)

    profile_data = {
        "user_id": user.id,
        "display_name": "DoxMind",
        "bio": "AI-powered documentation assistant that helps developers quickly understand and navigate technical documentation through intelligent Q&A and automatic summarization.",
        "tech_stack": [
            "Python",
            "TypeScript",
            "Next.js",
            "FastAPI",
            "PostgreSQL",
            "Redis",
            "Docker",
            "LLM",
            "RAG",
            "Vector Database"
        ],
        "experience_level": "intermediate",
        "availability_hours_per_week": 40,
        "timezone": "Asia/Shanghai",
        "preferred_team_size_min": 2,
        "preferred_team_size_max": 5,
        "goals": [
            "win_hackathons",
            "get_funding",
            "build_network",
            "learn_skills"
        ],
        "interests": [
            "AI/ML",
            "Developer Tools",
            "Productivity",
            "Documentation",
            "SaaS"
        ],
        "location_country": "China",
        "location_region": "Shanghai",
        "github_url": "https://github.com/doxmind",
        "portfolio_url": "https://doxmind.com",

        # Team/Company Info
        "team_name": "DoxMind",
        "team_size": 3,
        "company_stage": "mvp",

        # Product Info
        "product_name": "DoxMind",
        "product_description": "AI-powered documentation assistant that helps developers understand technical docs 10x faster through intelligent Q&A, auto-summarization, and multi-document analysis.",
        "product_url": "https://doxmind.com",
        "product_stage": "beta",

        # Funding
        "funding_stage": "bootstrapped",
        "seeking_funding": True,
        "funding_amount_seeking": "$100K - $500K",

        # Track Record
        "previous_hackathon_wins": 2,
        "notable_achievements": [
            "Built MVP in 3 months",
            "100+ beta users",
            "Featured on ProductHunt"
        ],
    }

    if existing_profile:
        print("Updating existing profile...")
        for key, value in profile_data.items():
            if key != "user_id":
                setattr(existing_profile, key, value)
        existing_profile.updated_at = datetime.now(timezone.utc)
        await existing_profile.save()
        print("Profile updated!")
    else:
        print("Creating new profile...")
        profile = Profile(**profile_data)
        await profile.insert()
        print("Profile created!")

    print("\n" + "=" * 50)
    print("DEMO ACCOUNT READY")
    print("=" * 50)
    print(f"Email:    {DEMO_EMAIL}")
    print(f"Password: {DEMO_PASSWORD}")
    print(f"Name:     {DEMO_FULL_NAME}")
    print("=" * 50)

    return user


if __name__ == "__main__":
    asyncio.run(create_demo_account())
