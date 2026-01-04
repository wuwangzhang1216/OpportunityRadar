#!/usr/bin/env python3
"""
Unified scraper entry point for OpportunityRadar.

Usage:
    python scripts/scrapers/run.py                    # Run all scrapers
    python scripts/scrapers/run.py --quick            # Run API-based scrapers only
    python scripts/scrapers/run.py --scrapers devpost mlh
    python scripts/scrapers/run.py --list             # List available scrapers
    python scripts/scrapers/run.py --test             # Test all scrapers
    python scripts/scrapers/run.py --update-details   # Update existing opportunities
"""

import argparse
import asyncio
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def main():
    parser = argparse.ArgumentParser(
        description="OpportunityRadar Scraper CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/scrapers/run.py                      # Populate from all scrapers
  python scripts/scrapers/run.py --quick              # Quick mode (API scrapers only)
  python scripts/scrapers/run.py -s devpost mlh       # Specific scrapers
  python scripts/scrapers/run.py --list               # List available scrapers
  python scripts/scrapers/run.py --test               # Test all scrapers
  python scripts/scrapers/run.py --update-details     # Update opportunity details
        """,
    )

    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--test", "-t", action="store_true", help="Test all scrapers without saving data"
    )
    mode_group.add_argument(
        "--update-details", "-u", action="store_true", help="Update existing opportunities with details"
    )
    mode_group.add_argument(
        "--list", "-l", action="store_true", help="List available scrapers and exit"
    )

    # Populate options
    parser.add_argument(
        "--scrapers", "-s", nargs="+", help="Specific scrapers to run (space-separated)"
    )
    parser.add_argument(
        "--pages", "-p", type=int, default=2, help="Max pages per scraper (default: 2)"
    )
    parser.add_argument(
        "--details", "-d", action="store_true", help="Fetch detailed info for each opportunity"
    )
    parser.add_argument(
        "--quick", "-q", action="store_true", help="Quick mode: only API-based scrapers"
    )

    args = parser.parse_args()

    # Handle different modes
    if args.list:
        run_list()
    elif args.test:
        run_test()
    elif args.update_details:
        run_update_details()
    else:
        run_populate(args)


def run_list():
    """List available scrapers."""
    from src.opportunity_radar.scrapers import ScraperRegistry

    PLAYWRIGHT_SCRAPERS = {"mlh", "ethglobal", "kaggle", "hackerearth", "sbir", "accelerators", "opensource_grants"}
    TYPE_MAPPING = {
        "devpost": "hackathon",
        "mlh": "hackathon",
        "ethglobal": "hackathon",
        "kaggle": "competition",
        "hackerearth": "hackathon",
        "grants_gov": "grant",
        "sbir": "grant",
        "eu_horizon": "grant",
        "innovate_uk": "grant",
        "hackerone": "bounty",
        "accelerators": "accelerator",
        "opensource_grants": "grant",
    }

    print("\nAvailable scrapers:")
    print("-" * 50)
    for name in sorted(ScraperRegistry.list_all()):
        scraper_type = TYPE_MAPPING.get(name, "other")
        driver = "Playwright" if name in PLAYWRIGHT_SCRAPERS else "HTTP"
        print(f"  {name:20} {scraper_type:12} [{driver}]")
    print()


def run_test():
    """Run scraper tests."""
    import subprocess
    script_path = os.path.join(os.path.dirname(__file__), "test_scrapers.py")
    subprocess.run([sys.executable, script_path])


def run_update_details():
    """Run detail updater."""
    import subprocess
    script_path = os.path.join(os.path.dirname(__file__), "update_opportunity_details.py")
    subprocess.run([sys.executable, script_path])


def run_populate(args):
    """Run populate script."""
    import subprocess
    script_path = os.path.join(os.path.dirname(__file__), "populate_all_opportunities.py")

    cmd = [sys.executable, script_path]

    if args.scrapers:
        cmd.extend(["--scrapers"] + args.scrapers)
    if args.pages:
        cmd.extend(["--pages", str(args.pages)])
    if args.details:
        cmd.append("--details")
    if args.quick:
        cmd.append("--quick")

    subprocess.run(cmd)


if __name__ == "__main__":
    main()
