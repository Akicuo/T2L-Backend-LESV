"""
Pytest configuration and fixtures
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator

from httpx import AsyncClient

# Import app lazily to avoid initialization issues
@pytest.fixture(scope="session")
def app():
    """Create FastAPI app for testing"""
    from main import app
    return app


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing"""
    # Use ASGI transport to properly test the FastAPI app
    from httpx._transports.asgi import ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(base_url="http://test", transport=transport) as ac:
        yield ac


@pytest.fixture
def valid_token() -> str:
    """Mock valid JWT token for testing"""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLWlkIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJwZXJzb25faWQiOm51bGwsInBlcnNvbl9uYW1lIjpudWxsfQ"


@pytest.fixture
def invalid_token() -> str:
    """Mock invalid JWT token for testing"""
    return "invalid.token.here"
