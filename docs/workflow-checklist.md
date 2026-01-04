# OpportunityRadar Workflow Guide + Checklist

This guide documents the end-to-end user workflow (product usage flow) plus a
local workflow checklist to validate the full stack and data pipelines.

## A) User Workflow (End-to-End)

This is the core user journey from first touch to ongoing usage. Use this
section when you want to *experience* the product as a user.

1) Landing -> Signup
- User sees product value and creates account.
- Backend: `POST /api/v1/auth/signup`

2) Login
- User logs in and receives access/refresh tokens.
- Backend: `POST /api/v1/auth/login`

3) Onboarding (3 steps)
- Step 1: Provide website/GitHub to extract profile.
  - Backend: `POST /api/v1/onboarding/extract`
- Step 2: User confirms/edits profile fields (tech stack, goals, constraints).
  - Backend: `POST /api/v1/onboarding/confirm`
- Step 3: Initial matching results shown.
  - Backend: `GET /api/v1/matches`

4) Opportunity Discovery
- User browses opportunities list with filters.
- Backend: `GET /api/v1/opportunities`

5) Matching + Bookmark/Dismiss
- User sees matched list and takes actions.
- Backend: `GET /api/v1/matches`
- Backend: `POST /api/v1/matches/{match_id}/bookmark`
- Backend: `POST /api/v1/matches/{match_id}/dismiss`

6) Pipeline Tracking
- User moves opportunity through states (discovered -> preparing -> submitted).
- Backend: `GET /api/v1/pipelines`
- Backend: `POST /api/v1/pipelines/{pipeline_id}/status`

7) Materials Generation
- User generates README/pitch/Q&A for a selected opportunity.
- Backend: `POST /api/v1/materials/generate`

8) Ongoing Usage
- Periodic scraping keeps opportunities fresh.
- User returns to review new matches and update pipeline status.

## B) User Journey Walkthrough (UI)

Use this runbook to step through the product in a real browser.

0) Prepare data (required for meaningful results)
- Run scrapers to populate opportunities:
  - `python scripts/scrapers/run.py --quick`
  - Optional: `python scripts/scrapers/populate_all_opportunities.py`

1) Landing -> Signup
- Visit `/` then `/signup`
- Expected: account created and redirected to onboarding.

2) Onboarding
- Step 1: Provide URL (GitHub/website) and submit.
- Step 2: Confirm extracted profile fields.
- Step 3: See initial matches.

3) Dashboard
- Visit `/dashboard`
- Expected: summary cards render; matched opportunities appear.

4) Opportunities
- Visit `/opportunities`
- Expected: list loads; filters work; open detail page `/opportunities/[id]`.

5) Pipeline
- Visit `/pipeline`
- Expected: move an opportunity between statuses.

6) Generator
- Visit `/generator`
- Expected: generate README/pitch/Q&A for a selected opportunity.

7) Profile
- Visit `/profile`
- Expected: updates persist and influence future matches.

## C) Local Workflow (Engineering)

### 1) Prerequisites

- Python 3.11+
- Node.js 18+
- Docker + Docker Compose
- Playwright dependencies (for browser scrapers)

### 2) Environment Setup

Backend `.env` (repo root):

```
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=opportunity_radar
OPENAI_API_KEY=...
JWT_SECRET_KEY=...
```

Frontend `frontend/.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8001
```

### 3) Start Dependencies (Databases)

Choose one:

```
docker-compose -f docker-compose.dev.yml up -d
```

or

```
./scripts/docker/start-docker.sh dev
```

### 4) Backend Workflow

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python scripts/db/init_db.py
python scripts/db/check_db_status.py

uvicorn src.opportunity_radar.main:app --reload --port 8001
```

### 5) Frontend Workflow

```
cd frontend
npm install
npm run dev
```

### 6) Data Pipeline (Optional)

Scrapers:

```
python scripts/scrapers/run.py --list
python scripts/scrapers/run.py --quick
```

Update details:

```
python scripts/scrapers/run.py --update-details --details
```

### 7) Tests and Code Quality

Backend:

```
pytest
pytest --cov=src/opportunity_radar
black src/ --line-length 100
ruff check src/
mypy src/
```

Frontend:

```
cd frontend
npm run lint
npm run build
```

### 8) Local Smoke Test

- Backend: http://localhost:8001/docs
- Frontend: http://localhost:3000
- Auth flow: signup/login
- Dashboard renders opportunities (if data seeded)

---

## Checklist

### User Workflow

- [ ] Signup completes and returns tokens.
- [ ] Login returns access/refresh tokens.
- [ ] Onboarding extract returns profile data.
- [ ] Onboarding confirm persists profile updates.
- [ ] Matches page shows initial results.
- [ ] Opportunities list loads and filters apply.
- [ ] Bookmark/dismiss updates match state.
- [ ] Pipeline status change persists.
- [ ] Materials generation returns content.
 - [ ] Profile edits persist and affect matches.

### Environment

- [ ] `.env` exists and contains `MONGODB_URL`, `MONGODB_DATABASE`,
  `OPENAI_API_KEY`, `JWT_SECRET_KEY`.
- [ ] `frontend/.env.local` exists and points `NEXT_PUBLIC_API_URL` to
  `http://localhost:8001`.

### Infra / Databases

- [ ] `docker-compose -f docker-compose.dev.yml up -d` starts successfully.
- [ ] `python scripts/db/check_db_status.py` reports MongoDB healthy.

### Backend

- [ ] `pip install -r requirements.txt` completes without errors.
- [ ] `uvicorn src.opportunity_radar.main:app --reload --port 8001` starts.
- [ ] Swagger docs load at `http://localhost:8001/docs`.
- [ ] Core endpoints respond:
  - [ ] `POST /api/v1/auth/signup`
  - [ ] `POST /api/v1/auth/login`
  - [ ] `GET /api/v1/opportunities`

### Frontend

- [ ] `npm install` completes without errors.
- [ ] `npm run dev` starts on port 3000.
- [ ] UI loads at `http://localhost:3000`.
- [ ] Auth flow works end-to-end with backend.

### Data / Scrapers (Optional)

- [ ] `python scripts/scrapers/run.py --list` returns scraper names.
- [ ] `python scripts/scrapers/run.py --quick` completes without errors.
- [ ] Opportunities appear in the dashboard after scraping.

### Tests / Quality

- [ ] `pytest` passes.
- [ ] `pytest --cov=src/opportunity_radar` meets coverage expectations.
- [ ] `black src/ --line-length 100` passes.
- [ ] `ruff check src/` passes.
- [ ] `mypy src/` passes.
- [ ] `npm run lint` passes.
- [ ] `npm run build` completes.

### Manual Verification (Optional)

- [ ] Run onboarding flow and confirm initial matches show.
- [ ] Generate materials via `/api/v1/materials/generate`.
- [ ] Pipeline status changes persist (discovered -> preparing -> submitted).
