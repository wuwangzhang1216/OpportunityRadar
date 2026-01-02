"""Test all scrapers."""

import asyncio
import logging
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


async def test_all():
    from src.opportunity_radar.scrapers import (
        # Original
        DevpostScraper, MLHScraper, ETHGlobalScraper, KaggleScraper, HackerEarthScraper,
        # New - Government
        GrantsGovScraper, SBIRScraper, EUHorizonScraper, InnovateUKScraper,
        # New - Other
        HackerOneScraper, YCombinatorScraper, OpenSourceGrantsScraper
    )

    scrapers = [
        # Original hackathon scrapers (already tested)
        ('Devpost', DevpostScraper(), 'hackathon'),
        ('MLH', MLHScraper(headless=True), 'hackathon'),
        ('ETHGlobal', ETHGlobalScraper(headless=True), 'hackathon'),
        ('Kaggle', KaggleScraper(headless=True), 'hackathon'),
        ('HackerEarth', HackerEarthScraper(headless=True), 'hackathon'),
        # New government funding scrapers
        ('Grants.gov', GrantsGovScraper(), 'gov-funding'),
        ('SBIR', SBIRScraper(headless=True), 'gov-funding'),
        ('EU Horizon', EUHorizonScraper(), 'gov-funding'),
        ('Innovate UK', InnovateUKScraper(), 'gov-funding'),
        # New other scrapers
        ('HackerOne', HackerOneScraper(), 'bug-bounty'),
        ('Accelerators', YCombinatorScraper(headless=True), 'accelerator'),
        ('OSS Grants', OpenSourceGrantsScraper(headless=True), 'oss-grants'),
    ]

    results = {}

    for name, scraper, category in scrapers:
        print(f'\nTesting {name} ({category})...')

        try:
            result = await scraper.scrape_list(page=1)
            results[name] = {
                'status': result.status.value,
                'count': result.total_found,
                'category': category
            }
            print(f'  Status: {result.status.value}, Found: {result.total_found}')

            # Show first 2 samples
            for opp in result.opportunities[:2]:
                title = opp.title[:50] + '...' if len(opp.title) > 50 else opp.title
                prize = f'${opp.total_prize_amount:,.0f}' if opp.total_prize_amount else 'N/A'
                print(f'    - {title} ({prize})')
        except Exception as e:
            results[name] = {'status': 'error', 'count': 0, 'category': category, 'error': str(e)[:50]}
            print(f'  Error: {str(e)[:100]}')
        finally:
            await scraper.close()

    # Summary
    print(f'\n{"="*60}')
    print('SUMMARY BY CATEGORY')
    print('='*60)

    categories = {}
    for name, r in results.items():
        cat = r['category']
        if cat not in categories:
            categories[cat] = {'total': 0, 'scrapers': []}
        categories[cat]['total'] += r['count']
        categories[cat]['scrapers'].append((name, r['count'], r['status']))

    grand_total = 0
    for cat, data in categories.items():
        print(f'\n{cat.upper()}:')
        for name, count, status in data['scrapers']:
            emoji = '[OK]' if status == 'success' else ('[WARN]' if status == 'partial' else '[ERR]')
            print(f'  {emoji} {name:15} | {count:4} opportunities')
        print(f'  {"":15} | {data["total"]:4} subtotal')
        grand_total += data['total']

    print(f'\n{"="*60}')
    print(f'GRAND TOTAL: {grand_total} opportunities')
    print('='*60)


if __name__ == "__main__":
    asyncio.run(test_all())
