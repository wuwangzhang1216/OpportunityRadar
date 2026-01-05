"""Clean up all demo user data for fresh testing."""

import asyncio
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Demo Account Email
DEMO_EMAIL = "demo@doxmind.com"


async def cleanup_demo_data():
    """Delete all data associated with demo user."""
    from src.opportunity_radar.db.mongodb import init_db
    from src.opportunity_radar.models.user import User
    from src.opportunity_radar.models.profile import Profile
    from src.opportunity_radar.models.match import Match
    from src.opportunity_radar.models.pipeline import Pipeline
    from src.opportunity_radar.models.material import Material
    from src.opportunity_radar.models.notification import Notification

    # Initialize database
    print("Connecting to database...")
    await init_db()
    print("Connected!")

    # Find demo user
    user = await User.find_one(User.email == DEMO_EMAIL)
    if not user:
        print(f"Demo user not found: {DEMO_EMAIL}")
        return

    user_id = user.id
    print(f"\nFound demo user: {DEMO_EMAIL} (ID: {user_id})")
    print("=" * 50)

    # Delete all related data
    stats = {}

    # 1. Delete Matches
    print("\n1. Deleting Matches...")
    result = await Match.find(Match.user_id == user_id).delete()
    stats["matches"] = result.deleted_count if result else 0
    print(f"   Deleted {stats['matches']} matches")

    # 2. Delete Pipelines
    print("\n2. Deleting Pipelines...")
    result = await Pipeline.find(Pipeline.user_id == user_id).delete()
    stats["pipelines"] = result.deleted_count if result else 0
    print(f"   Deleted {stats['pipelines']} pipelines")

    # 3. Delete Materials
    print("\n3. Deleting Materials...")
    result = await Material.find(Material.user_id == user_id).delete()
    stats["materials"] = result.deleted_count if result else 0
    print(f"   Deleted {stats['materials']} materials")

    # 4. Delete Notifications
    print("\n4. Deleting Notifications...")
    result = await Notification.find(Notification.user_id == user_id).delete()
    stats["notifications"] = result.deleted_count if result else 0
    print(f"   Deleted {stats['notifications']} notifications")

    # 5. Delete Profile
    print("\n5. Deleting Profile...")
    result = await Profile.find(Profile.user_id == user_id).delete()
    stats["profiles"] = result.deleted_count if result else 0
    print(f"   Deleted {stats['profiles']} profiles")

    # 6. Delete User
    print("\n6. Deleting User...")
    await user.delete()
    stats["users"] = 1
    print(f"   Deleted user: {DEMO_EMAIL}")

    # Summary
    print("\n" + "=" * 50)
    print("CLEANUP COMPLETE")
    print("=" * 50)
    for key, count in stats.items():
        print(f"  {key}: {count}")
    print("=" * 50)

    return stats


if __name__ == "__main__":
    asyncio.run(cleanup_demo_data())
