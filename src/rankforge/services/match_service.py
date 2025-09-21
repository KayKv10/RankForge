# src/rankforge/services/match_service.py

"""Business logic for match-related operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from rankforge.db import models
from rankforge.rating import dummy_engine
from rankforge.schemas import match as match_schema


async def process_new_match(
    db: AsyncSession, match_in: match_schema.MatchCreate
) -> models.Match:
    """
    Processes the creation of a new match.

    This service is responsible for:
    1. Creating the Match and MatchParticipant records in the database.
    2. Triggering the rating calculation process.
    3. Updating player profiles with new ratings and stats.
    """
    # 1. Create the database models from the input schema
    #    We exclude 'participants' because that's a list of schemas, not a direct field
    match_data = match_in.model_dump(exclude={"participants"})
    new_match = models.Match(**match_data)

    # 2. Create MatchParticipant objects for each participant in the payload.
    for participant_data in match_in.participants:
        new_participant = models.MatchParticipant(**participant_data.model_dump())
        new_match.participants.append(new_participant)

    # 3. Add the new match and its particpants to the session and commit.
    db.add(new_match)
    await db.commit()
    await db.refresh(new_match)

    # 4. Trigger the rating update process
    await dummy_engine.update_ratings_for_match(db, new_match)

    # 5. Re-query the match to eager load all relationships for the response
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
