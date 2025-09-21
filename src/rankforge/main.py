# src/rankforge/main.py

"""Main FastAPI application for RankForge."""


from fastapi import FastAPI

from .api import game, match, player

app = FastAPI(title="RankForge API")

# Include routers into the main application
app.include_router(game.router)
app.include_router(player.router)
app.include_router(match.router)


@app.get("/", tags=["Root"])
async def read_root() -> dict[str, str]:
    """Provides a welcome message."""
    return {"message": "Welcome to the RankForge API"}
