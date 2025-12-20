# src/rankforge/services/match_service.py

"""Business logic for match-related operations."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from rankforge.db import models
from rankforge.rating import dummy_engine, glicko2_engine
from rankforge.schemas import match as match_schema

logger = logging.getLogger(__name__)

# A default rating structure for new players in a game.
# NOTE: This will be eventually configured per-game
DEFAULT_RATING_INFO = {"rating": 1500.0, "rd": 350.0, "vol": 0.06}


async def get_or_create_game_profile(
    db: AsyncSession, player_id: int, game_id: int
) -> models.GameProfile:
    """
    Retrieves a player's game profile, creating it with default
    values if it doesn't exist.
    """
    # Attempt to fetch an existing profile.
    query = select(models.GameProfile).where(
        models.GameProfile.player_id == player_id,
        models.GameProfile.game_id == game_id,
    )
    result = await db.execute(query)
    profile = result.scalar_one_or_none()

    # If no profile exists, create a new one.
    if profile is None:
        profile = models.GameProfile(
            player_id=player_id,
            game_id=game_id,
            rating_info=DEFAULT_RATING_INFO,
            stats={},  # Start with empty stats
        )
        db.add(profile)
        # NOTE: We don't commit here; the main function will handle the commit.
        # We need to flush to get the profile object ready for use.
        await db.flush()
    return profile


async def process_new_match(
    db: AsyncSession, match_in: match_schema.MatchCreate
) -> models.Match:
    """
    Processes the creation of a new match.

    This service is responsible for:
    1. Creating the Match and MatchParticipant records in the database.
    2. Triggering the rating calculation process.
    3. Updating player profiles with new ratings and stats.

    All operations are performed within a single transaction. If any step
    fails, the entire transaction is rolled back to maintain data consistency.
    """
    try:
        # 1. Fetch the game and determine the rating strategy
        game = await db.get(models.Game, match_in.game_id)
        if not game:
            raise ValueError(f"Game with ID {match_in.game_id} not found")

        # 2. Create the database models from the input schema.
        #    Exclude 'participants' as it's a list of schemas, not a direct field.
        match_data = match_in.model_dump(exclude={"participants"})
        new_match = models.Match(**match_data)

        # 3. Ensure profiles exist and create participant records.
        for participant_data in match_in.participants:
            profile = await get_or_create_game_profile(
                db, player_id=participant_data.player_id, game_id=match_in.game_id
            )

            # Store the "before" rating for historical tracking
            participant_with_history = participant_data.model_dump()
            participant_with_history["rating_info_before"] = profile.rating_info

            new_participant = models.MatchParticipant(**participant_with_history)
            new_match.participants.append(new_participant)

        # 4. Add the new match and flush to get IDs (NO COMMIT YET)
        db.add(new_match)
        await db.flush()
        await db.refresh(new_match, attribute_names=["participants"])

        # 5. DISPATCHER: Trigger the correct rating update process.
        #    Rating engines use flush(), not commit(), to allow atomic transactions.
        if game.rating_strategy == "glicko2":
            await glicko2_engine.update_ratings_for_match(db, new_match)
        else:
            # Default to dummy engine or handle as an error
            await dummy_engine.update_ratings_for_match(db, new_match)

        # 6. COMMIT the entire transaction atomically (match + ratings together)
        await db.commit()

        # 7. Re-query the match to eager load all relationships for the response.
        result = await db.execute(
            select(models.Match)
            .where(models.Match.id == new_match.id)
            .options(
                selectinload(models.Match.participants).selectinload(
                    models.MatchParticipant.player
                )
            )
        )
        created_match = result.scalar_one()

        return created_match

    except Exception as e:
        logger.error(f"Failed to process match, rolling back: {e}")
        await db.rollback()
        raise
