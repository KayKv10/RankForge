# src/rankforge/main.py

"""Main FastAPI application for RankForge."""

from fastapi import FastAPI

app = FastAPI(title="RankForge API")


@app.get("/")
def read_root() -> dict[str, str]:
    """Provides a welcome message for the API root."""
    return {"message": "Welcome to the RankForge API"}
