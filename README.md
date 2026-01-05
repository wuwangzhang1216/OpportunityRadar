# OpportunityRadar

> Your intelligent opportunity radar for startups and developers

OpportunityRadar helps you discover, match, prepare for, and win opportunities that accelerate your growth — government grants, hackathons, startup competitions, accelerators, and pitch events.

## Features

### Core Features
- **Smart Discovery**: Aggregates opportunities from multiple sources (Kaggle, Devpost, MLH, government grants, etc.)
- **Intelligent Matching**: Matches opportunities to your profile using semantic similarity + eligibility rules
- **Material Generation**: AI-powered generation of READMEs, pitch decks, demo scripts, and Q&A predictions
- **Pipeline Tracking**: Track your opportunities from discovery to submission to results

### User Experience
- **Personalized Match Scores**: See match percentages with detailed score breakdowns (relevance, eligibility, timeline, team fit)
- **Eligibility Checking**: Visual indicators showing which requirements you meet and suggestions to improve
- **Quick Actions**: Bookmark, dismiss, or add opportunities to pipeline with hover actions
- **Drag-and-Drop Pipeline**: Move opportunities between stages by dragging cards
- **Materials Library**: View, copy, and manage all your AI-generated materials in one place

### Workflow
- **3-Step Onboarding**: Quick profile setup with URL extraction and instant matches
- **Dashboard Overview**: See top matches, pipeline stats, and quick actions at a glance
- **Calendar Integration**: Add deadlines to Google Calendar, Outlook, or download .ics files

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: MongoDB (Beanie ODM)
- **AI/ML**: OpenAI embeddings for semantic matching
- **Scrapers**: Playwright-based scrapers for multiple platforms

### Frontend
- **Framework**: Next.js 14 with App Router
- **Styling**: Tailwind CSS
- **State**: Zustand + TanStack Query
- **UI Components**: Custom components with Radix UI primitives
- **Animations**: Framer Motion

## Project Structure

```
OpportunityRadar/
├── src/opportunity_radar/     # Backend Python package
│   ├── api/                   # FastAPI routes
│   │   └── v1/endpoints/      # API endpoints
│   ├── ai/                    # AI/LLM integration
│   ├── scrapers/              # Platform scrapers
│   ├── matching/              # Matching engine
│   ├── models/                # Beanie/MongoDB models
│   ├── schemas/               # Pydantic schemas
│   ├── services/              # Business logic
│   └── repositories/          # Data access layer
├── frontend/                  # Next.js frontend
│   ├── app/                   # App router pages
│   │   ├── (auth)/            # Auth pages (login, signup, onboarding)
│   │   ├── (dashboard)/       # Main app pages
│   │   └── (admin)/           # Admin panel
│   ├── components/            # React components
│   ├── services/              # API client
│   └── stores/                # Zustand stores
├── docker/                    # Docker configs
├── scripts/                   # Utility scripts
└── docs/                      # Documentation
```

## Frontend Pages

| Route | Description |
|-------|-------------|
| `/dashboard` | Main dashboard with stats, top matches, and quick actions |
| `/opportunities` | Browse all opportunities with match scores and filters |
| `/opportunities/[id]` | Opportunity detail with match breakdown and eligibility |
| `/pipeline` | Kanban board to track opportunity progress |
| `/generator` | AI material generator for README, pitch, demo scripts |
| `/materials` | Library of all generated materials |
| `/profile` | User profile and preferences |
| `/teams` | Team management and collaboration |
| `/community` | Public shared opportunity lists |
| `/notifications` | Notification center |
| `/settings` | Account settings |

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- MongoDB (or use Docker)

### Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Start databases with Docker
docker-compose -f docker-compose.dev.yml up -d

# Run backend
uvicorn src.opportunity_radar.main:app --reload --port 8001
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Database
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=opportunity_radar

# AI
OPENAI_API_KEY=your_openai_key

# Auth
JWT_SECRET_KEY=your_jwt_secret

# OAuth (optional)
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

Frontend `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8001
```

## Scrapers

Currently supported platforms:
- Kaggle Competitions
- Devpost Hackathons
- MLH Hackathons
- ETHGlobal Events
- HackerEarth Challenges
- Government Grants (Grants.gov, SBIR, EU Horizon, Innovate UK)
- Y Combinator RFS

## API Endpoints

### Auth
- `POST /api/v1/auth/signup` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user
- `GET /api/v1/auth/oauth/{provider}/authorize` - OAuth login

### Opportunities
- `GET /api/v1/opportunities` - List opportunities
- `GET /api/v1/opportunities/{id}` - Get opportunity detail

### Matches
- `GET /api/v1/matches` - Get matched opportunities (with scores)
- `GET /api/v1/matches/top` - Get top N matches
- `GET /api/v1/matches/by-batch/{batch_id}` - Get match for specific opportunity
- `POST /api/v1/matches/{id}/bookmark` - Bookmark a match
- `POST /api/v1/matches/{id}/dismiss` - Dismiss a match

### Pipeline
- `GET /api/v1/pipelines` - Get user's pipeline items
- `POST /api/v1/pipelines` - Add opportunity to pipeline
- `POST /api/v1/pipelines/{id}/stage/{stage}` - Move to stage
- `DELETE /api/v1/pipelines/{id}` - Remove from pipeline

### Materials
- `POST /api/v1/materials/generate` - Generate materials
- `GET /api/v1/materials` - List generated materials
- `DELETE /api/v1/materials/{id}` - Delete material

### Profile
- `GET /api/v1/profiles/me` - Get user profile
- `PUT /api/v1/profiles/me` - Update profile

## Development

### Running Tests

```bash
# Backend
pytest
pytest --cov=src/opportunity_radar

# Frontend
cd frontend
npm run lint
npm run build
```

### Code Quality

```bash
# Backend
black src/ --line-length 100
ruff check src/
mypy src/

# Frontend
npm run lint
```

## Documentation

- [Design Document](docs/design.md) - Full system design and architecture
- [Workflow Checklist](docs/workflow-checklist.md) - End-to-end workflow guide
- [Roadmap](docs/ROADMAP.md) - Feature roadmap

## License

MIT
