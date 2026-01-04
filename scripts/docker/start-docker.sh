#!/bin/bash
# Start OpportunityRadar with Docker

set -e

echo "=========================================="
echo "  OpportunityRadar Docker Startup"
echo "=========================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from template..."
    cp .env.docker .env
    echo "Please edit .env with your settings (especially OPENAI_API_KEY)"
fi

# Parse arguments
MODE=${1:-dev}

case $MODE in
    dev)
        echo "Starting development services (DB + Redis only)..."
        docker-compose -f docker-compose.dev.yml up -d
        echo ""
        echo "Services started:"
        echo "  - PostgreSQL: localhost:5432"
        echo "  - Redis: localhost:6379"
        echo "  - Adminer: http://localhost:8080"
        echo ""
        echo "Now run the backend and frontend locally:"
        echo "  Backend:  uvicorn src.opportunity_radar.main:app --reload"
        echo "  Frontend: cd frontend && npm run dev"
        ;;

    full)
        echo "Starting all services..."
        docker-compose up -d --build
        echo ""
        echo "Services started:"
        echo "  - Backend API: http://localhost:8000"
        echo "  - Frontend: http://localhost:3000"
        echo "  - PostgreSQL: localhost:5432"
        echo "  - Redis: localhost:6379"
        echo ""
        echo "API Docs: http://localhost:8000/docs"
        ;;

    down)
        echo "Stopping all services..."
        docker-compose down
        docker-compose -f docker-compose.dev.yml down
        echo "All services stopped."
        ;;

    logs)
        docker-compose logs -f
        ;;

    *)
        echo "Usage: $0 [dev|full|down|logs]"
        echo "  dev  - Start only DB and Redis (for local development)"
        echo "  full - Start all services including backend and frontend"
        echo "  down - Stop all services"
        echo "  logs - View logs"
        exit 1
        ;;
esac
