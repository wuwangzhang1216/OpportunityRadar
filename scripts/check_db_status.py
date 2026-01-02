#!/usr/bin/env python3
"""Check database status and current data counts."""

import asyncio
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def check_mongodb():
    """Check MongoDB connection and data counts."""
    from motor.motor_asyncio import AsyncIOMotorClient
    from beanie import init_beanie
    from src.opportunity_radar.config import settings

    print("=" * 60)
    print("MongoDB Status Check")
    print("=" * 60)
    print(f"URL: {settings.mongodb_url}")
    print(f"Database: {settings.mongodb_database}")
    print()

    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(settings.mongodb_url)

        # Test connection
        await client.admin.command("ping")
        print("[OK] MongoDB connection successful")

        # Initialize Beanie
        from src.opportunity_radar.models.user import User
        from src.opportunity_radar.models.profile import Profile
        from src.opportunity_radar.models.opportunity import Opportunity, Host
        from src.opportunity_radar.models.match import Match
        from src.opportunity_radar.models.pipeline import Pipeline
        from src.opportunity_radar.models.material import Material

        await init_beanie(
            database=client[settings.mongodb_database],
            document_models=[User, Profile, Host, Opportunity, Match, Pipeline, Material],
        )

        # Count documents in each collection
        print("\n" + "-" * 60)
        print("Document Counts:")
        print("-" * 60)

        counts = {
            "Users": await User.find().count(),
            "Profiles": await Profile.find().count(),
            "Hosts": await Host.find().count(),
            "Opportunities": await Opportunity.find().count(),
            "Matches": await Match.find().count(),
            "Pipelines": await Pipeline.find().count(),
            "Materials": await Material.find().count(),
        }

        for name, count in counts.items():
            status = "[OK]" if count > 0 else "[EMPTY]"
            print(f"  {status} {name:15} : {count:6}")

        # Opportunity breakdown by type
        opp_count = counts["Opportunities"]
        if opp_count > 0:
            print("\n" + "-" * 60)
            print("Opportunities by Type:")
            print("-" * 60)

            pipeline = [{"$group": {"_id": "$opportunity_type", "count": {"$sum": 1}}}]
            db = client[settings.mongodb_database]
            type_counts = await db.opportunities.aggregate(pipeline).to_list(length=100)
            for doc in type_counts:
                opp_type = doc["_id"] or "unknown"
                print(f"  - {opp_type:20} : {doc['count']:6}")

            # Recent opportunities
            print("\n" + "-" * 60)
            print("Recent 5 Opportunities:")
            print("-" * 60)

            recent = await Opportunity.find().sort("-created_at").limit(5).to_list()
            for opp in recent:
                title = opp.title[:45] + "..." if len(opp.title) > 45 else opp.title
                print(f"  - {title}")
                print(f"    Type: {opp.opportunity_type}, Prize: ${opp.total_prize_value or 0:,.0f}")

        client.close()
        return True

    except Exception as e:
        print(f"[ERROR] MongoDB check failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    mongo_ok = await check_mongodb()

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"MongoDB: {'[OK]' if mongo_ok else '[FAILED]'}")

    if not mongo_ok:
        print("\nTroubleshooting:")
        print("  1. Ensure MongoDB is running: docker-compose -f docker-compose.dev.yml up -d")
        print("  2. Check .env file has correct MONGODB_URL")


if __name__ == "__main__":
    asyncio.run(main())
