# src/rankforge/rating/dummy_engine.py

"""A dummy rating engine for testing the service layer architecture."""

from sqlalchemy.ext.asyncio import AsyncSession

from rankforge.db import models


async def update_ratings_for_match(db: AsyncSession, match: models.Match) -> None:
    """
    A placeholder rating update function.

    This dummy implementation will eventually be replaced by real rating engines
    like Glicko-2. Its purpose is to prove that the service layer can
    correctly call a rating update function after a match is created.
    """
    # NOTE: Rating logic will be implemented here.
    print(f"Dummy rating engine called for match_id: {match.id}")
    pass
