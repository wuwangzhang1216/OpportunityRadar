@echo off
REM Start OpportunityRadar with Docker

echo ==========================================
echo   OpportunityRadar Docker Startup
echo ==========================================

REM Check if .env exists
if not exist .env (
    echo Creating .env from template...
    copy .env.docker .env
    echo Please edit .env with your settings (especially OPENAI_API_KEY)
)

REM Parse arguments
set MODE=%1
if "%MODE%"=="" set MODE=dev

if "%MODE%"=="dev" goto dev
if "%MODE%"=="full" goto full
if "%MODE%"=="down" goto down
if "%MODE%"=="logs" goto logs
goto usage

:dev
echo Starting development services (MongoDB + PostgreSQL + Redis)...
docker-compose -f docker-compose.dev.yml up -d
echo.
echo Services started:
echo   - MongoDB: localhost:27017
echo   - PostgreSQL: localhost:5432
echo   - Redis: localhost:6380
echo   - Adminer: http://localhost:8080
echo.
echo Now run the backend and frontend locally:
echo   Backend:  uvicorn src.opportunity_radar.main:app --reload
echo   Frontend: cd frontend ^&^& npm run dev
goto end

:full
echo Starting all services...
docker-compose up -d --build
echo.
echo Services started:
echo   - Backend API: http://localhost:8000
echo   - Frontend: http://localhost:3000
echo   - PostgreSQL: localhost:5432
echo   - Redis: localhost:6379
echo.
echo API Docs: http://localhost:8000/docs
goto end

:down
echo Stopping all services...
docker-compose down
docker-compose -f docker-compose.dev.yml down
echo All services stopped.
goto end

:logs
docker-compose logs -f
goto end

:usage
echo Usage: %0 [dev^|full^|down^|logs]
echo   dev  - Start only DB and Redis (for local development)
echo   full - Start all services including backend and frontend
echo   down - Stop all services
echo   logs - View logs
exit /b 1

:end
