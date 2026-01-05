"""Pytest configuration and fixtures."""

import asyncio
import os
import sys
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Use asyncio backend."""
    return "asyncio"


@pytest_asyncio.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for API testing."""
    from src.opportunity_radar.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="session")
def mongodb_url() -> str:
    """Get MongoDB URL from environment or default."""
    return os.getenv("MONGODB_URL", "mongodb://localhost:27017")


@pytest.fixture(scope="session")
def test_settings():
    """Get test settings."""
    from src.opportunity_radar.config import get_settings

    return get_settings()
