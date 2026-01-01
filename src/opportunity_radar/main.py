"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .core.exceptions import AppException
from .api.v1.router import api_router
from .db.mongodb import init_db, close_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
# Set our app's logger to DEBUG for more detail
logging.getLogger("src.opportunity_radar").setLevel(logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    print(f"Starting {settings.app_name}...")
    await init_db()
    print("MongoDB connected successfully")
    yield
    # Shutdown
    print(f"Shutting down {settings.app_name}...")
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="Intelligent opportunity radar for developers - discover, match, and prepare for hackathons",
        version="0.1.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.message,
                "details": exc.details,
            },
        )

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "app": settings.app_name}

    # Include API router
    app.include_router(api_router, prefix="/api")

    return app


app = create_app()
