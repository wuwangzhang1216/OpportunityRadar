# P0: Opportunity Crawler

> **Priority**: P0 (Blocking)
> **Status**: `COMPLETED`
> **Progress**: 100%
> **Last Updated**: 2026-01-03

## Completion Summary

**513 opportunities** collected from 12 sources:

| Source | Type | Count |
|--------|------|-------|
| MLH | hackathon | 195 |
| ETHGlobal | hackathon | 79 |
| Devpost | hackathon | 48 |
| Grants.gov | grant | 50 |
| HackerOne | bounty | 50 |
| Kaggle | competition | 35 |
| Accelerators | accelerator | 14 |
| Open Source Grants | grant | 16 |
| EU Horizon | grant | 11 |
| Innovate UK | grant | 10 |
| SBIR | grant | 8 |
| HackerEarth | hackathon | 0 (site blocked) |

Scripts created:
- `scripts/check_db_status.py` - Database status check
- `scripts/populate_all_opportunities.py` - Data population
- `scripts/test_scrapers.py` - Fixed path issues

---

## Overview

Build an automated crawler system to collect opportunity data (hackathons, grants, accelerators, bounties, competitions) from various platforms.

---

## Why This Matters

- **Blocking Issue**: Without opportunity data, the entire platform is empty
- **Core Dependency**: Matching, pipeline, and materials features all depend on having opportunities
- **User Value**: Users come to discover opportunities they wouldn't find otherwise

---

## Target Data Sources

### Phase 1 - High Priority

| Source | Type | URL | Difficulty |
|--------|------|-----|------------|
| Devpost | Hackathons | devpost.com | Medium |
| MLH | Hackathons | mlh.io | Easy |
| Gitcoin | Bounties/Grants | gitcoin.co | Medium |
| DoraHacks | Hackathons/Grants | dorahacks.io | Medium |
| ETHGlobal | Hackathons | ethglobal.com | Easy |

### Phase 2 - Medium Priority

| Source | Type | URL | Difficulty |
|--------|------|-----|------------|
| Y Combinator | Accelerator | ycombinator.com | Hard |
| Techstars | Accelerator | techstars.com | Medium |
| Product Hunt | Launches | producthunt.com | Medium |
| AngelList | Accelerators | angel.co | Medium |

### Phase 3 - Nice to Have

| Source | Type | URL | Difficulty |
|--------|------|-----|------------|
| Grants.gov | Government Grants | grants.gov | Hard |
| EU Horizon | Grants | ec.europa.eu | Hard |
| Foundation Grants | Various | Multiple | Hard |

---

## Data Schema

Each opportunity should capture:

```python
class Opportunity:
    # Core Fields
    title: str
    description: str
    category: Literal["hackathon", "grant", "bounty", "accelerator", "competition"]

    # Source
    source_platform: str          # e.g., "devpost", "mlh"
    source_url: str               # Original listing URL

    # Dates
    deadline: datetime | None
    start_date: datetime | None
    end_date: datetime | None

    # Rewards
    prize_pool: str | None        # e.g., "$50,000", "Equity"
    prize_details: list[str]      # Breakdown of prizes

    # Requirements
    team_size_min: int | None
    team_size_max: int | None
    eligibility: list[str]        # e.g., ["students", "US-based"]

    # Technical
    tech_stack: list[str]         # e.g., ["AI", "Web3", "Mobile"]
    themes: list[str]             # e.g., ["Climate", "Healthcare"]

    # Location
    location: str | None          # "Online" or city/country
    is_remote: bool

    # Meta
    organizer: str | None
    sponsors: list[str]

    # Crawler Meta
    crawled_at: datetime
    batch_id: str
    is_active: bool
```

---

## Technical Architecture

### Components

```
┌─────────────────────────────────────────────────────┐
│                  Crawler Service                     │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   Devpost   │  │     MLH     │  │   Gitcoin   │ │
│  │   Crawler   │  │   Crawler   │  │   Crawler   │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │
│         │                │                │         │
│         └────────────────┼────────────────┘         │
│                          │                          │
│                  ┌───────▼───────┐                  │
│                  │   Normalizer   │                  │
│                  │   & Deduper    │                  │
│                  └───────┬───────┘                  │
│                          │                          │
│                  ┌───────▼───────┐                  │
│                  │   Enrichment   │                  │
│                  │   (AI/LLM)     │                  │
│                  └───────┬───────┘                  │
│                          │                          │
└──────────────────────────┼──────────────────────────┘
                           │
                   ┌───────▼───────┐
                   │    MongoDB     │
                   │  Opportunities │
                   └───────────────┘
```

### Key Design Decisions

1. **Separate crawlers per source** - Each platform has unique structure
2. **Common normalization layer** - Standardize data before storage
3. **AI enrichment** - Use LLM to extract/categorize missing fields
4. **Deduplication** - Prevent duplicate opportunities across sources
5. **Batch tracking** - Track which crawl run added each opportunity

---

## Implementation Tasks

### Phase 1: Foundation

- [ ] Create crawler base class with common utilities
- [ ] Set up httpx async client with rate limiting
- [ ] Create MongoDB batch tracking collection
- [ ] Build normalization pipeline
- [ ] Add deduplication logic (URL + title matching)

### Phase 2: First Crawlers

- [ ] Implement Devpost crawler
- [ ] Implement MLH crawler
- [ ] Implement ETHGlobal crawler
- [ ] Test end-to-end flow
- [ ] Add error handling and retry logic

### Phase 3: AI Enrichment

- [ ] Extract tech stack from descriptions
- [ ] Categorize by themes
- [ ] Parse prize details
- [ ] Generate embeddings for matching

### Phase 4: Scheduling

- [ ] Set up cron/scheduled jobs
- [ ] Add monitoring and alerts
- [ ] Create crawler health dashboard

---

## API Endpoints (Admin)

```
POST /api/v1/admin/crawlers/run
  - Run specific crawler manually

GET /api/v1/admin/crawlers/status
  - Get status of all crawlers

GET /api/v1/admin/batches
  - List all crawl batches

POST /api/v1/admin/opportunities/import
  - Manual bulk import via CSV/JSON
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Total opportunities crawled | 500+ |
| Sources integrated | 5+ |
| Data freshness | < 24 hours |
| Crawl success rate | > 95% |
| Deduplication accuracy | > 99% |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Site structure changes | Crawler breaks | Modular crawlers, easy to update |
| Rate limiting/blocking | Can't fetch data | Respectful delays, rotating proxies |
| Data quality issues | Bad matching | AI validation, manual review |
| Legal/ToS concerns | Service issues | Only public data, respect robots.txt |

---

## Dependencies

- None (this is the foundation)

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-03 | Initial plan created |
