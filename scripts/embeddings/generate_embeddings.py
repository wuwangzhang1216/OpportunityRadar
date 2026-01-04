#!/usr/bin/env python3
"""
Generate embeddings for opportunities in the database.

Usage:
    python scripts/embeddings/generate_embeddings.py               # Generate for all without embeddings
    python scripts/embeddings/generate_embeddings.py --force       # Regenerate all
    python scripts/embeddings/generate_embeddings.py --dry-run     # Preview without generating
    python scripts/embeddings/generate_embeddings.py --stats       # Show embedding statistics only
    python scripts/embeddings/generate_embeddings.py --batch-size 50  # Custom batch size
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def get_embedding_stats():
    """Get and display embedding statistics."""
    from src.opportunity_radar.models.opportunity import Opportunity

    total = await Opportunity.find().count()
    with_embeddings = await Opportunity.find(Opportunity.embedding != None).count()  # noqa: E711
    without_embeddings = total - with_embeddings

    percentage = (with_embeddings / total * 100) if total > 0 else 0

    print("\n" + "=" * 50)
    print("Embedding Statistics")
    print("=" * 50)
    print(f"Total opportunities:    {total:>6}")
    print(f"With embeddings:        {with_embeddings:>6} ({percentage:.1f}%)")
    print(f"Without embeddings:     {without_embeddings:>6}")
    print("=" * 50 + "\n")

    return {
        "total": total,
        "with_embeddings": with_embeddings,
        "without_embeddings": without_embeddings,
    }


async def generate_embeddings(
    force: bool = False,
    dry_run: bool = False,
    batch_size: int = 50,
    limit: int = 0,
):
    """Generate embeddings for opportunities."""
    from src.opportunity_radar.models.opportunity import Opportunity
    from src.opportunity_radar.services.embedding_service import get_embedding_service

    # Build query
    if force:
        query = {}
        logger.info("Force mode: regenerating all embeddings")
    else:
        query = {"embedding": None}
        logger.info("Generating embeddings for opportunities without embeddings")

    # Get opportunities
    opportunities_query = Opportunity.find(query)
    if limit > 0:
        opportunities_query = opportunities_query.limit(limit)

    opportunities = await opportunities_query.to_list()

    if not opportunities:
        print("\nNo opportunities found that need embeddings.")
        return

    print(f"\nFound {len(opportunities)} opportunities to process")

    if dry_run:
        print("\n[DRY RUN] Would generate embeddings for:")
        for i, opp in enumerate(opportunities[:10], 1):
            print(f"  {i}. {opp.title[:60]}...")
        if len(opportunities) > 10:
            print(f"  ... and {len(opportunities) - 10} more")
        print("\nNo changes made.")
        return

    # Get embedding service
    embedding_service = get_embedding_service()

    # Prepare opportunities for batch processing
    opp_dicts = []
    for opp in opportunities:
        opp_dicts.append({
            "id": str(opp.id),
            "title": opp.title,
            "description": opp.description,
            "short_description": opp.short_description,
            "themes": opp.themes,
            "technologies": opp.technologies,
            "category": opp.opportunity_type,
        })

    print(f"\nGenerating embeddings with batch size {batch_size}...")
    start_time = datetime.now()

    # Generate embeddings
    results, stats = embedding_service.generate_opportunity_embeddings_batch(
        opp_dicts,
        batch_size=batch_size,
    )

    # Save embeddings to database
    success = 0
    failed = 0

    for result in results:
        if result.success:
            try:
                from beanie import PydanticObjectId
                opp_id = PydanticObjectId(result.id)
                await Opportunity.find_one({"_id": opp_id}).update(
                    {"$set": {"embedding": result.embedding, "updated_at": datetime.utcnow()}}
                )
                success += 1
            except Exception as e:
                logger.error(f"Failed to save embedding for {result.id}: {e}")
                failed += 1
        else:
            logger.error(f"Failed to generate embedding for {result.id}: {result.error}")
            failed += 1

    elapsed = (datetime.now() - start_time).total_seconds()

    # Print summary
    print("\n" + "=" * 50)
    print("Embedding Generation Complete")
    print("=" * 50)
    print(f"Total processed:    {len(opportunities)}")
    print(f"Success:            {success}")
    print(f"Failed:             {failed}")
    print(f"Skipped:            {stats.get('skipped', 0)}")
    print(f"Time elapsed:       {elapsed:.1f}s")
    print(f"Rate:               {len(opportunities) / elapsed:.1f} ops/sec")
    print("=" * 50 + "\n")


async def main():
    parser = argparse.ArgumentParser(
        description="Generate embeddings for opportunities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force regenerate embeddings for all opportunities",
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Preview changes without generating embeddings",
    )
    parser.add_argument(
        "--stats", "-s",
        action="store_true",
        help="Show embedding statistics only",
    )
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        default=50,
        help="Number of opportunities per batch (default: 50)",
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=0,
        help="Limit number of opportunities to process (0 = no limit)",
    )

    args = parser.parse_args()

    # Initialize MongoDB
    from src.opportunity_radar.db.mongodb import init_db

    print("Connecting to MongoDB...")
    await init_db()
    print("Connected!")

    if args.stats:
        await get_embedding_stats()
    else:
        # Show stats before
        await get_embedding_stats()

        # Generate embeddings
        await generate_embeddings(
            force=args.force,
            dry_run=args.dry_run,
            batch_size=args.batch_size,
            limit=args.limit,
        )

        # Show stats after (unless dry run)
        if not args.dry_run:
            await get_embedding_stats()


if __name__ == "__main__":
    asyncio.run(main())
