"""Pytest configuration and fixtures."""
import asyncio
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from rankforge.db.models import Base
from rankforge.main import app, get_db
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL)
AsyncTestingSessionLocal = async_sessionmaker(
    bind=engine, expire_on_commit=False, autocommit=False, autoflush=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for our test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """Fixture to create and tear down the test database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Fixture to provide a database session to a test."""
    async with AsyncTestingSessionLocal() as session:
        yield session


@pytest.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Fixture to provide an async test client for the API."""

    # Override the get_db dependency to use the test database
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Clean up the override after the test
    del app.dependency_overrides[get_db]
