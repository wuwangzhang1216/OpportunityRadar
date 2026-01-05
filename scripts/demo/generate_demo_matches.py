"""Generate matches for demo user."""

import asyncio
import sys
import os

# Fix Windows encoding issues
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Demo Account Email
DEMO_EMAIL = "demo@doxmind.com"


async def generate_demo_matches():
    """Generate matches for demo user using the matching service."""
    from src.opportunity_radar.db.mongodb import init_db
    from src.opportunity_radar.models.user import User
    from src.opportunity_radar.models.profile import Profile
    from src.opportunity_radar.services.mongo_matching_service import MongoMatchingService

    # Initialize database
    print("Connecting to database...")
    await init_db()
    print("Connected!")

    # Find demo user
    user = await User.find_one(User.email == DEMO_EMAIL)
    if not user:
        print(f"Demo user not found: {DEMO_EMAIL}")
        return

    # Find profile
    profile = await Profile.find_one(Profile.user_id == user.id)
    if not profile:
        print(f"Profile not found for demo user")
        return

    print(f"\nFound profile: {profile.display_name}")
    print(f"  Goals: {profile.goals}")
    print(f"  Tech Stack: {profile.tech_stack[:3]}...")
    print(f"  Has Embedding: {profile.embedding is not None}")

    # Create matching service and compute matches
    print("\nComputing matches...")
    matching_service = MongoMatchingService()

    try:
        matches = await matching_service.compute_matches_for_profile(
            profile_id=str(profile.id),
            limit=100,
            min_score=0.0
        )

        print(f"\n✅ Generated {len(matches)} matches!")

        # Show top 5 matches
        if matches:
            print("\nTop 5 matches:")
            for i, match in enumerate(matches[:5]):
                print(f"  {i+1}. Score: {match.score:.1%}")
                if hasattr(match, 'breakdown') and match.breakdown:
                    bd = match.breakdown
                    print(f"      - Semantic: {bd.semantic_score:.1%}")
                    print(f"      - Tech Overlap: {bd.tech_overlap_score:.1%}")
                    print(f"      - Industry: {bd.industry_alignment_score:.1%}")
                    print(f"      - Goals: {bd.goals_alignment_score:.1%}")
                    print(f"      - Deadline: {bd.deadline_score:.1%}")

        # Save matches - use user_id, not profile_id!
        print("\nSaving matches to database...")
        saved_count = await matching_service.save_matches(str(user.id), matches)
        print(f"✅ Saved {saved_count} matches!")

    except Exception as e:
        print(f"❌ Error computing matches: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 50)
    print("MATCH GENERATION COMPLETE")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(generate_demo_matches())
