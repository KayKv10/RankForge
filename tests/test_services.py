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


@pytest.mark.asyncio
async def test_process_new_match_updates_player_stats(db_session: AsyncSession):
    """
    Verify that the full match processing pipeline calls the rating engine
    and that the engine's changes are persisted to the database.
    """
    # 1. SETUP: Create a game, player, and a pre-existing GameProfile.
    game = Game(name="Stat Test Game", rating_strategy="test")
    player = Player(name="StatPlayer")
    db_session.add_all([game, player])
    await db_session.commit()

    # The player's profile shows they have played 5 matches already.
    profile = GameProfile(
        player_id=player.id,
        game_id=game.id,
        rating_info={"rating": 1550},
        stats={"matches_played": 5},
    )
    db_session.add(profile)
    await db_session.commit()

    # 2. PREPARE INPUT: Create the Pydantic schema for the new match.
    match_in = MatchCreate(
        game_id=game.id,
        participants=[
            MatchParticipantCreate(
                player_id=player.id, team_id=1, outcome={"result": "win"}
            )
        ],
    )

    # 3. EXECUTE: Call the service function.
    await match_service.process_new_match(db=db_session, match_in=match_in)

    # 4. ASSERT: Verify that the stats in the database have been updated.
    await db_session.refresh(profile)

    # Assert that the 'matches_played' stat was correctly incremented.
    assert profile.stats is not None
    assert "matches_played" in profile.stats
    assert (
        profile.stats["matches_played"] == 6
    ), "The dummy engine did not increment the matches_played stat."


@pytest.mark.asyncio
async def test_process_new_match_updates_glicko2_ratings(db_session: AsyncSession):
    """
    Verify that for a Glicko-2 game, the match service calls the correct
    engine and updates the winner's and loser's ratings appropriately.
    """
    # 1. ARRANGE: Set up the game, players, and their initial profiles.
    #    The `rating_strategy` is key here for the future dispatcher.
    game = Game(name="Glicko-2 Game", rating_strategy="glicko2")
    winner = Player(name="Winner")
    loser = Player(name="Loser")
    db_session.add_all([game, winner, loser])
    await db_session.commit()

    # Create pre-existing profiles with default Glicko-2 ratings.
    initial_rating_info = {"rating": 1500.0, "rd": 300.0, "vol": 0.06}
    winner_profile = GameProfile(
        player_id=winner.id, game_id=game.id, rating_info=initial_rating_info.copy()
    )
    loser_profile = GameProfile(
        player_id=loser.id, game_id=game.id, rating_info=initial_rating_info.copy()
    )
    db_session.add_all([winner_profile, loser_profile])
    await db_session.commit()

    # Capture the initial rating values for comparison.
    winner_initial_rating: float = winner_profile.rating_info["rating"]
    loser_initial_rating: float = loser_profile.rating_info["rating"]

    # 2. ACT: Prepare and process the match payload via the service.
    match_in = MatchCreate(
        game_id=game.id,
        participants=[
            MatchParticipantCreate(
                player_id=winner.id, team_id=1, outcome={"result": "win"}
            ),
            MatchParticipantCreate(
                player_id=loser.id, team_id=2, outcome={"result": "loss"}
            ),
        ],
    )
    await match_service.process_new_match(db=db_session, match_in=match_in)

    # 3. ASSERT: Verify that the ratings in the database have changed as expected.
    await db_session.refresh(winner_profile)
    await db_session.refresh(loser_profile)

    # Assert that the winner's rating has increased.
    assert (
        winner_profile.rating_info["rating"] > winner_initial_rating
    ), "Winner's rating should increase"

    # Assert that the loser's rating has decreased.
    assert (
        loser_profile.rating_info["rating"] < loser_initial_rating
    ), "Loser's rating should decrease"

    # A key property of Glicko-2 is that Rating Deviation (RD) should change
    # after a match. It usually decreases.
    assert (
        winner_profile.rating_info["rd"] != initial_rating_info["rd"]
    ), "Winner's rating deviation should change"
    assert (
        loser_profile.rating_info["rd"] != initial_rating_info["rd"]
    ), "Loser's rating deviation should change"
