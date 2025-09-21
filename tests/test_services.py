# tests/test_services.py

"""Unit tests for the service layer."""

import pytest
from rankforge.db.models import Game, GameProfile, Player
from rankforge.schemas.match import MatchCreate, MatchParticipantCreate
from rankforge.services import match_service
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_process_new_match_creates_game_profiles(db_session: AsyncSession):
    """
    Verify that processing a new match creates GameProfile entries for
    participants who don't already have one for that game.
    """
    # 1. SETUP: Create a game and two players.
    #    Crucially, these players have NO GameProfile for this game yet.
    game = Game(name="Test Game", rating_strategy="test")
    player1 = Player(name="FirstTimer")
    player2 = Player(name="Veteran")  # Will also be a first-timer in this test
    db_session.add_all([game, player1, player2])
    await db_session.commit()

    # Create a GameProfile for player2 in a *different* game to ensure
    # our logic is specific.
    other_game = Game(name="Other Game", rating_strategy="other")
    db_session.add(other_game)
    await db_session.commit()
    # This existing profile should NOT be affected.
    veteran_other_profile = GameProfile(
        player_id=player2.id, game_id=other_game.id, rating_info={"rating": 1500}
    )
    db_session.add(veteran_other_profile)
    await db_session.commit()

    # 2. PREPARE INPUT: Create the Pydantic schema for the new match.
    match_in = MatchCreate(
        game_id=game.id,
        participants=[
            MatchParticipantCreate(
                player_id=player1.id, team_id=1, outcome={"result": "win"}
            ),
            MatchParticipantCreate(
                player_id=player2.id, team_id=2, outcome={"result": "loss"}
            ),
        ],
    )

    # 3. EXECUTE: Call the service function directly..
    await match_service.process_new_match(db=db_session, match_in=match_in)

    # 4. ASSERT: Check that the GameProfiles were created correctly.
    #    Query for the GameProfile for player1 in the new game.
    profile1_query = await db_session.execute(
        select(GameProfile).where(
            GameProfile.player_id == player1.id, GameProfile.game_id == game.id
        )
    )
    created_profile1 = profile1_query.scalar_one_or_none()

    # Assert that the profile was created.
    assert created_profile1 is not None, "GameProfile for player1 was not created"

    # NOTE: Will add assertions for  initial rating later.
    # For now, just confirming it's not empty.
    assert created_profile1.rating_info is not None

    # Query for the GameProfile for player2 in the new game.
    profile2_query = await db_session.execute(
        select(GameProfile).where(
            GameProfile.player_id == player2.id, GameProfile.game_id == game.id
        )
    )
    created_profile2 = profile2_query.scalar_one_or_none()
    assert created_profile2 is not None, "GameProfile for player2 was not created"

    # Finally, ensure that the total number of profiles for player2 is now 2.
    all_profiles_p2_query = await db_session.execute(
        select(GameProfile).where(GameProfile.player_id == player2.id)
    )
    all_profiles_p2 = all_profiles_p2_query.scalars().all()
    assert len(all_profiles_p2) == 2, "Incorrect total number of profiles for player2"
