# OpportunityRadar Workflow Guide + Checklist

This guide documents the end-to-end user workflow (product usage flow) plus a
local workflow checklist to validate the full stack and data pipelines.

## A) User Workflow (End-to-End)

This is the core user journey from first touch to ongoing usage. Use this
section when you want to *experience* the product as a user.

### 1) Landing -> Signup
- User sees product value and creates account.
- Backend: `POST /api/v1/auth/signup`

### 2) Login
- User logs in and receives access/refresh tokens.
- Backend: `POST /api/v1/auth/login`
- OAuth options: GitHub, Google

### 3) Onboarding (3 steps)
- Step 1: Provide website/GitHub to extract profile.
  - Backend: `POST /api/v1/onboarding/extract`
- Step 2: User confirms/edits profile fields (tech stack, goals, constraints).
  - Backend: `POST /api/v1/onboarding/confirm`
- Step 3: Initial matching results shown with "What's Next?" guidance.
  - Backend: `GET /api/v1/matches`
  - Quick actions: Go to Dashboard, Try AI Generator, View Pipeline

### 4) Dashboard
- User sees summary stats: Total Matches, In Pipeline, Preparing, Won
- Top Matches displayed with match scores
- Pipeline Overview showing stage counts
- Quick Actions for common tasks

### 5) Opportunity Discovery
- User browses opportunities list with personalized match scores.
- Filters: All Matches, Bookmarked, Dismissed
- Category filters: Hackathons, Grants, Bounties, Accelerators, Competitions
- Backend: `GET /api/v1/matches` (personalized)
- Quick actions on hover: Bookmark, Dismiss, Add to Pipeline

### 6) Opportunity Detail
- User views full opportunity details with match breakdown.
- Match Score Card showing:
  - Overall score percentage
  - Score breakdown (Relevance, Eligibility, Timeline, Team Fit)
  - Eligibility status (eligible/partial/ineligible)
  - Improvement suggestions
- Actions: Bookmark, Dismiss, Add to Pipeline, Generate Materials, Add to Calendar
- Backend: `GET /api/v1/opportunities/{id}`
- Backend: `GET /api/v1/matches/by-batch/{batch_id}`

### 7) Matching + Bookmark/Dismiss
- User manages opportunities with quick actions.
- Backend: `POST /api/v1/matches/{match_id}/bookmark`
- Backend: `POST /api/v1/matches/{match_id}/unbookmark`
- Backend: `POST /api/v1/matches/{match_id}/dismiss`
- Backend: `POST /api/v1/matches/{match_id}/restore`

### 8) Pipeline Tracking
- Kanban board with 6 stages: Discovered, Preparing, Submitted, Pending, Won, Lost
- Drag-and-drop cards between stages
- Right-click menu for quick actions:
  - Move to any stage
  - Generate Materials
  - Mark as Won
  - Archive (move to Lost)
  - Delete permanently
- Archived section with restore/delete options
- Backend: `GET /api/v1/pipelines`
- Backend: `POST /api/v1/pipelines/{pipeline_id}/stage/{stage}`
- Backend: `DELETE /api/v1/pipelines/{pipeline_id}`

### 9) Materials Generation
- User generates README/pitch/Q&A for a selected opportunity.
- Supports URL parameters: `?batch_id={id}` or `?opportunity_id={id}`
- Material types: README, 1/3/5-min Pitch, Demo Script, Q&A Predictions
- Backend: `POST /api/v1/materials/generate`

### 10) Materials Library
- User views all previously generated materials.
- Actions: Expand/collapse, Copy to clipboard, Delete
- Backend: `GET /api/v1/materials`
- Backend: `DELETE /api/v1/materials/{id}`

### 11) Ongoing Usage
- Periodic scraping keeps opportunities fresh.
- User returns to review new matches and update pipeline status.
- Profile updates influence future matches.

## B) User Journey Walkthrough (UI)

Use this runbook to step through the product in a real browser.

### 0) Prepare data (required for meaningful results)
- Run scrapers to populate opportunities:
  - `python scripts/scrapers/run.py --quick`
  - Optional: `python scripts/scrapers/populate_all_opportunities.py`

### 1) Landing -> Signup
- Visit `/` then `/signup`
- Expected: account created and redirected to onboarding.

### 2) Onboarding
- Step 1: Provide URL (GitHub/website) and submit.
- Step 2: Confirm extracted profile fields.
- Step 3: See initial matches with "What's Next?" guidance.
- Quick actions available: Go to Dashboard, Try AI Generator, View Pipeline

### 3) Dashboard
- Visit `/dashboard`
- Expected: summary cards render; top matches appear with scores.

### 4) Opportunities
- Visit `/opportunities`
- Expected: personalized list with match scores; filters work.
- Hover over cards to see quick actions (bookmark, dismiss, add to pipeline).
- Click card to view `/opportunities/[id]` with match breakdown.

### 5) Opportunity Detail
- Visit `/opportunities/[id]`
- Expected: match score card with breakdown, eligibility status, suggestions.
- Actions: bookmark, dismiss, add to pipeline, generate materials, calendar.

### 6) Pipeline
- Visit `/pipeline`
- Expected: kanban board with drag-and-drop.
- Drag cards between stages.
- Right-click for menu options.
- Archived items show at bottom with restore/delete.

### 7) Generator
- Visit `/generator` or `/generator?batch_id=[id]`
- Expected: generate materials; context auto-fills if batch_id provided.

### 8) Materials
- Visit `/materials`
- Expected: list of generated materials; expand, copy, delete.

### 9) Profile
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
- [ ] OAuth login works (GitHub/Google).
- [ ] Onboarding extract returns profile data.
- [ ] Onboarding confirm persists profile updates.
- [ ] Onboarding Step 3 shows matches and "What's Next?" guidance.
- [ ] Dashboard shows stats and top matches with scores.
- [ ] Opportunities list shows personalized matches with scores.
- [ ] Quick actions work: bookmark, dismiss, add to pipeline.
- [ ] Opportunity detail shows match breakdown and eligibility.
- [ ] Bookmark/unbookmark updates match state.
- [ ] Dismiss/restore updates match state.
- [ ] Pipeline kanban loads with stages.
- [ ] Drag-and-drop moves cards between stages.
- [ ] Right-click menu works for stage changes.
- [ ] Archive moves item to Lost stage.
- [ ] Delete permanently removes from pipeline.
- [ ] Archived items can be restored.
- [ ] Generator loads context from batch_id parameter.
- [ ] Materials generation returns content.
- [ ] Materials page lists generated content.
- [ ] Materials can be copied and deleted.
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
  - [ ] `GET /api/v1/matches`
  - [ ] `GET /api/v1/matches/by-batch/{batch_id}`
  - [ ] `POST /api/v1/matches/{id}/bookmark`
  - [ ] `GET /api/v1/pipelines`
  - [ ] `DELETE /api/v1/pipelines/{id}`
  - [ ] `GET /api/v1/materials`

### Frontend

- [ ] `npm install` completes without errors.
- [ ] `npm run dev` starts on port 3000.
- [ ] UI loads at `http://localhost:3000`.
- [ ] Auth flow works end-to-end with backend.
- [ ] All navigation items work:
  - [ ] Dashboard
  - [ ] Opportunities
  - [ ] Pipeline
  - [ ] AI Generator
  - [ ] My Materials
  - [ ] Teams
  - [ ] Community
  - [ ] Submissions
  - [ ] Notifications
  - [ ] Profile
  - [ ] Settings

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
- [ ] Verify match score breakdown on opportunity detail page.
- [ ] Test bookmark/dismiss from opportunities list.
- [ ] Test drag-and-drop in pipeline.
- [ ] Test right-click menu in pipeline.
- [ ] Generate materials via `/generator?batch_id={id}`.
- [ ] Verify materials appear in `/materials`.
- [ ] Pipeline status changes persist (discovered -> preparing -> submitted).
