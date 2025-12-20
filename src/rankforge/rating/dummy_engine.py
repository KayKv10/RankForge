# src/rankforge/rating/dummy_engine.py

"""A dummy rating engine for testing the service layer architecture."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rankforge.db import models


async def update_ratings_for_match(db: AsyncSession, match: models.Match) -> None:
    """
    A placeholder rating update function.

    This dummy implementation will eventually be replaced by real rating engines
    like Glicko-2. Its purpose is to prove that the service layer can
    correctly call a rating update function after a match is created.

    This dummy implementation finds the GameProfile for each participant and
    increments their 'matches_played' stat. This proves the end-to-end
    pipeline from service to engine to database update.
    """
    # Loop through each participant in the match object that was passed in.
    for participant in match.participants:
        query = select(models.GameProfile).where(
            models.GameProfile.player_id == participant.player_id,
            models.GameProfile.game_id == match.game_id,
        )
        result = await db.execute(query)
        profile = result.scalar_one()

        # Get the current stat value, defaulting to 0 if it doesn't exist.
        current_matches_played = profile.stats.get("matches_played", 0)

        # Increment the stat.
        new_stats = profile.stats.copy()  # Create a copy to modify
        new_stats["matches_played"] = current_matches_played + 1

        # Update the profile's stats field with the new dictionary.
        profile.stats = new_stats

        # Add the modified profile to the session to mark it for an UPDATE.
        db.add(profile)

    # Flush changes but don't commit - let the caller handle transaction boundaries
    await db.flush()
