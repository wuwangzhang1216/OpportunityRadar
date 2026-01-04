# OpportunityRadar Scripts

Scripts for managing the OpportunityRadar system.

## Directory Structure

```
scripts/
├── scrapers/          # Web scraping scripts
│   ├── run.py                          # Unified entry point
│   ├── populate_all_opportunities.py   # Populate DB from scrapers
│   ├── update_opportunity_details.py   # Update existing opportunities
│   └── test_scrapers.py                # Test all scrapers
├── db/                # Database management
│   ├── init_db.py                      # Initialize PostgreSQL
│   ├── create_tables.sql               # SQL table definitions
│   └── check_db_status.py              # Check MongoDB status
├── admin/             # User management
│   └── create_admin.py                 # Create/promote admin users
├── docker/            # Container management
│   ├── start-docker.sh                 # Linux/Mac startup
│   └── start-docker.bat                # Windows startup
└── tests/             # Integration tests
    └── test_system.py                  # System integration tests
```

## Quick Start

### 1. Start Services (Docker)

```bash
# Linux/Mac
./scripts/docker/start-docker.sh dev

# Windows
scripts\docker\start-docker.bat dev
```

### 2. Initialize Database

```bash
python scripts/db/init_db.py
```

### 3. Run Scrapers

```bash
# Run all scrapers
python scripts/scrapers/run.py

# Quick mode (API-based scrapers only, faster)
python scripts/scrapers/run.py --quick

# Specific scrapers
python scripts/scrapers/run.py --scrapers devpost mlh hackerone

# List available scrapers
python scripts/scrapers/run.py --list

# Test scrapers without saving
python scripts/scrapers/run.py --test
```

### 4. Check Status

```bash
python scripts/db/check_db_status.py
```

## Scraper Commands

| Command | Description |
|---------|-------------|
| `run.py` | Unified entry point |
| `run.py --list` | List all available scrapers |
| `run.py --quick` | Run API-based scrapers only |
| `run.py --scrapers X Y` | Run specific scrapers |
| `run.py --test` | Test scrapers without DB |
| `run.py --update-details` | Update existing records |
| `run.py --pages N` | Set max pages (default: 2) |
| `run.py --details` | Fetch full details |

## Available Scrapers

| Name | Type | Driver | Notes |
|------|------|--------|-------|
| devpost | hackathon | HTTP | Fast, API-based |
| mlh | hackathon | Playwright | |
| ethglobal | hackathon | Playwright | |
| kaggle | competition | Playwright | |
| hackerearth | hackathon | Playwright | |
| grants_gov | grant | HTTP | US government grants |
| sbir | grant | Playwright | Small business grants |
| eu_horizon | grant | HTTP | EU research grants |
| innovate_uk | grant | HTTP | UK innovation grants |
| hackerone | bounty | HTTP | Bug bounties |
| accelerators | accelerator | Playwright | YCombinator |
| opensource_grants | grant | Playwright | |

## Admin Commands

```bash
# Create new admin user
python scripts/admin/create_admin.py admin@example.com password123

# Promote existing user to admin
python scripts/admin/create_admin.py existing@example.com
```

## Docker Modes

```bash
# Dev mode: DB + Redis only (for local development)
./scripts/docker/start-docker.sh dev

# Full mode: All services including backend/frontend
./scripts/docker/start-docker.sh full

# Stop all services
./scripts/docker/start-docker.sh down

# View logs
./scripts/docker/start-docker.sh logs
```
