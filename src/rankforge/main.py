# src/rankforge/main.py

"""Main FastAPI application for RankForge."""

from typing import AsyncGenerator

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from .db.session import AsyncSessionLocal

app = FastAPI(title="RankForge API")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides an async database session."""
    async with AsyncSessionLocal() as session:
        yield session


@app.get("/")
async def read_root(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Provides a welcome message and confirms database connectivity."""
    is_db_connected = "successfully" if db else "failed"
    return {
        "message": "Welcome to the RankForge API",
        "database_connection": f"Session created {is_db_connected}",
    }
