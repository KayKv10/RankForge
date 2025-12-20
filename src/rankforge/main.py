# src/rankforge/main.py

"""Main FastAPI application for RankForge."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api import game, match, player
from .db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup and shutdown events."""
    # Startup: Nothing special needed, engine is created on import
    yield
    # Shutdown: Dispose of database connections gracefully
    await engine.dispose()


app = FastAPI(title="RankForge API", lifespan=lifespan)

# Include routers into the main application
app.include_router(game.router)
app.include_router(player.router)
app.include_router(match.router)


@app.get("/", tags=["Root"])
async def read_root() -> dict[str, str]:
    """Provides a welcome message."""
    return {"message": "Welcome to the RankForge API"}


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}
