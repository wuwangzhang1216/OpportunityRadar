# OpportunityRadar

> Your intelligent opportunity radar for startups and developers

OpportunityRadar helps you discover, match, prepare for, and win opportunities that accelerate your growth — government grants, hackathons, startup competitions, accelerators, and pitch events.

## Features

- **Smart Discovery**: Aggregates opportunities from multiple sources (Kaggle, Devpost, MLH, government grants, etc.)
- **Intelligent Matching**: Matches opportunities to your profile using semantic similarity + eligibility rules
- **Material Generation**: AI-powered generation of READMEs, pitch decks, demo scripts, and Q&A predictions
- **Pipeline Tracking**: Track your opportunities from discovery to submission to results

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Databases**: PostgreSQL + MongoDB
- **AI/ML**: OpenAI embeddings for semantic matching
- **Scrapers**: Playwright-based scrapers for multiple platforms

### Frontend
- **Framework**: Next.js 14 with App Router
- **Styling**: Tailwind CSS
- **State**: Zustand
- **UI Components**: Custom components with Radix UI primitives

## Project Structure

```
OpportunityRadar/
├── src/opportunity_radar/     # Backend Python package
│   ├── api/                   # FastAPI routes
│   ├── ai/                    # AI/LLM integration
│   ├── scrapers/              # Platform scrapers
│   ├── matching/              # Matching engine
│   ├── models/                # SQLAlchemy models
│   ├── schemas/               # Pydantic schemas
│   ├── services/              # Business logic
│   └── repositories/          # Data access layer
├── frontend/                  # Next.js frontend
│   ├── app/                   # App router pages
│   ├── components/            # React components
│   ├── services/              # API client
│   └── stores/                # Zustand stores
├── docker/                    # Docker configs
├── migrations/                # Alembic migrations
└── scripts/                   # Utility scripts
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL & MongoDB (or use Docker)

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
DATABASE_URL=postgresql://user:pass@localhost:5432/opportunity_radar
MONGODB_URL=mongodb://localhost:27017

# AI
OPENAI_API_KEY=your_openai_key

# Auth
JWT_SECRET=your_jwt_secret
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

- `POST /api/v1/auth/signup` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/opportunities` - List opportunities
- `GET /api/v1/matches` - Get matched opportunities
- `POST /api/v1/materials/generate` - Generate materials
- `GET /api/v1/pipelines` - Get user pipelines

## License

MIT
