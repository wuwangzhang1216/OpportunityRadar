# OpportunityRadar Roadmap

> **Core Value**: AI-powered opportunity matching for startup teams
> **Target Users**: Early-stage startup teams seeking accelerators, grants, and hackathons
> **Last Updated**: 2026-01-03

---

## Overview

This document tracks the implementation plan for OpportunityRadar's core features. Each feature has a dedicated plan document in `docs/plans/`.

---

## Priority Matrix

### P0 - Blocking (Must Have First)

| Feature | Plan | Status | Progress |
|---------|------|--------|----------|
| Opportunity Crawler | [P0-opportunity-crawler.md](./plans/P0-opportunity-crawler.md) | `COMPLETED` | 100% |
| Admin Dashboard | [P0-admin-dashboard.md](./plans/P0-admin-dashboard.md) | `COMPLETE` | 100% |

### P1 - Core Experience

| Feature | Plan | Status | Progress |
|---------|------|--------|----------|
| Team Profile Enhancement | [P1-team-profile.md](./plans/P1-team-profile.md) | `NOT_STARTED` | 0% |
| Matching Algorithm Optimization | [P1-matching-algorithm.md](./plans/P1-matching-algorithm.md) | `NOT_STARTED` | 0% |
| Deadline Reminders | [P1-deadline-reminder.md](./plans/P1-deadline-reminder.md) | `NOT_STARTED` | 0% |

### P2 - Experience Enhancement

| Feature | Plan | Status | Progress |
|---------|------|--------|----------|
| OAuth Login (GitHub/Google) | TBD | `NOT_STARTED` | 0% |
| Team Collaboration | TBD | `NOT_STARTED` | 0% |
| Material Generation Improvements | TBD | `NOT_STARTED` | 0% |
| Enhanced Opportunity Details | TBD | `NOT_STARTED` | 0% |

### P3 - Growth Features

| Feature | Plan | Status | Progress |
|---------|------|--------|----------|
| User-submitted Opportunities | TBD | `NOT_STARTED` | 0% |
| Calendar Integration | TBD | `NOT_STARTED` | 0% |
| Data Export | TBD | `NOT_STARTED` | 0% |
| Community/Sharing | TBD | `NOT_STARTED` | 0% |

---

## Implementation Order

```
Phase 1: Data Foundation
├── [1] Opportunity Crawler      ✅ COMPLETED (513 opportunities)
└── [2] Admin Dashboard          🔄 IN PROGRESS (Backend ✅, Frontend pending)

Phase 2: Core Value
├── [3] Team Profile Enhancement
├── [4] Matching Algorithm Optimization
└── [5] Deadline Reminders

Phase 3: Growth Ready
├── [6] OAuth Login
├── [7] Team Collaboration
└── [8] Material Generation Improvements
```

---

## Status Legend

| Status | Meaning |
|--------|---------|
| `NOT_STARTED` | Planning not begun |
| `PLANNING` | Design/architecture phase |
| `IN_PROGRESS` | Active development |
| `TESTING` | QA and bug fixes |
| `COMPLETED` | Deployed to production |
| `BLOCKED` | Waiting on dependency |

---

## Current Sprint Focus

**Phase 1: Data Foundation**

~~1. **Opportunity Crawler** - Automated data collection from major platforms~~ ✅ DONE

~~2. **Admin Dashboard Backend** - API endpoints for data management~~ ✅ DONE

Next priority:

3. **Admin Dashboard Frontend** - UI for opportunity/crawler/user management

---

## Session Notes (2026-01-03)

### What Was Done Today

1. **P0: Opportunity Crawler** - COMPLETED
   - Fixed `scripts/test_scrapers.py` path issue (was hardcoded Windows path)
   - Created `scripts/check_db_status.py` for database monitoring
   - Created `scripts/populate_all_opportunities.py` for data population
   - Installed Playwright browsers (Firefox + Chromium)
   - Tested all 12 scrapers, 11 working (HackerEarth blocked)
   - Populated database with **513 opportunities**

2. **Database Status**
   - 319 hackathons, 95 grants, 50 bounties, 35 competitions, 14 accelerators
   - 1 user, 1 profile (test data)

### Tomorrow's Tasks

1. **P0: Admin Dashboard** - See [P0-admin-dashboard.md](./plans/P0-admin-dashboard.md)
   - Add admin role to User model
   - Create admin API endpoints
   - Build admin UI (opportunities CRUD, crawler management)

### Quick Commands

```bash
# Check database status
.venv/bin/python scripts/check_db_status.py

# Run all scrapers
.venv/bin/python scripts/populate_all_opportunities.py --pages 2

# Run specific scrapers
.venv/bin/python scripts/populate_all_opportunities.py -s devpost mlh

# Quick mode (API scrapers only)
.venv/bin/python scripts/populate_all_opportunities.py --quick

# Start backend
uvicorn src.opportunity_radar.main:app --reload --port 8001

# Start frontend
cd frontend && npm run dev
```

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-03 | P0 Admin Dashboard Backend completed - 15 endpoints, ScraperRun model (PR #1) |
| 2026-01-03 | P0 Opportunity Crawler completed - 513 opportunities from 12 sources |
| 2026-01-03 | Initial roadmap created |
