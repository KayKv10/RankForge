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


@pytest.mark.asyncio
async def test_process_new_match_handles_ranked_outcomes(db_session: AsyncSession):
    """
    Verify that the Glicko-2 engine correctly processes ranked outcomes
    (e.g., 1st, 2nd, 3rd) and updates ratings accordingly.
    """
    # 1. ARRANGE: Set up a 4-player FFA game and their profiles.
    game = Game(name="FFA Game", rating_strategy="glicko2")
    players = [Player(name=f"Player {i+1}") for i in range(4)]
    db_session.add(game)
    db_session.add_all(players)
    await db_session.commit()

    # Give everyone a slightly different starting rating for more robust testing.
    initial_ratings = [1550.0, 1500.0, 1450.0, 1400.0]
    profiles = []
    for i, player in enumerate(players):
        profile = GameProfile(
            player_id=player.id,
            game_id=game.id,
            rating_info={"rating": initial_ratings[i], "rd": 200.0, "vol": 0.06},
        )
        profiles.append(profile)
    db_session.add_all(profiles)
    await db_session.commit()

    # 2. ACT: Process a match where the players finish in reverse order of rating.
    # Player 4 (1400 rating) gets 1st, Player 3 gets 2nd, etc.
    # This should result in significant rating changes.
    match_in = MatchCreate(
        game_id=game.id,
        participants=[
            MatchParticipantCreate(
                player_id=players[0].id, team_id=1, outcome={"rank": 4}
            ),  # 1550 -> 4th
            MatchParticipantCreate(
                player_id=players[1].id, team_id=2, outcome={"rank": 3}
            ),  # 1500 -> 3rd
            MatchParticipantCreate(
                player_id=players[2].id, team_id=3, outcome={"rank": 2}
            ),  # 1450 -> 2nd
            MatchParticipantCreate(
                player_id=players[3].id, team_id=4, outcome={"rank": 1}
            ),  # 1400 -> 1st
        ],
    )
    await match_service.process_new_match(db=db_session, match_in=match_in)

    # 3. ASSERT: Verify the new ratings follow a logical progression.
    new_ratings = []
    for i, profile in enumerate(profiles):
        await db_session.refresh(profile)
        new_ratings.append(profile.rating_info["rating"])

    # The 1st place winner (lowest rated player) should have a large rating gain.
    p4_rating_change = new_ratings[3] - initial_ratings[3]
    assert p4_rating_change > 0, "1st place should gain rating"

    # The 4th place loser (highest rated player) should have a large rating loss.
    p1_rating_change = new_ratings[0] - initial_ratings[0]
    assert p1_rating_change < 0, "4th place should lose rating"

    # The 1st place player should gain more rating than the 2nd place player.
    p3_rating_change = new_ratings[2] - initial_ratings[2]
    assert p4_rating_change > p3_rating_change, "1st place should gain more than 2nd"

    # The 4th place player should lose more rating than the 3rd place player.
    p2_rating_change = new_ratings[1] - initial_ratings[1]
    assert p1_rating_change < p2_rating_change, "4th place should lose more than 3rd"


@pytest.mark.asyncio
async def test_process_new_match_handles_ranked_outcomes_2(db_session: AsyncSession):
    """
    Verify that the Glicko-2 engine correctly processes ranked outcomes
    (e.g., 1st, 2nd, 3rd) and updates ratings accordingly. This test uses a
    scenario where a "draw" result would be incorrect.
    """
    # 1. ARRANGE: Set up a 4-player FFA game and their profiles.
    game = Game(name="FFA Game 2", rating_strategy="glicko2")
    players = [Player(name=f"RankedPlayer {i+1}") for i in range(4)]
    db_session.add(game)
    db_session.add_all(players)
    await db_session.commit()

    # Players are rated from highest to lowest.
    initial_ratings = [1550.0, 1500.0, 1450.0, 1400.0]
    profiles = []
    for i, player in enumerate(players):
        profile = GameProfile(
            player_id=player.id,
            game_id=game.id,
            rating_info={"rating": initial_ratings[i], "rd": 200.0, "vol": 0.06},
        )
        profiles.append(profile)
    db_session.add_all(profiles)
    await db_session.commit()

    # 2. ACT: Process a match where the players finish according to their rating.
    # Player 1 (highest rated) gets 1st, Player 4 (lowest rated) gets 4th.
    match_in = MatchCreate(
        game_id=game.id,
        participants=[
            MatchParticipantCreate(
                player_id=players[0].id, team_id=1, outcome={"rank": 1}
            ),  # 1550 -> 1st
            MatchParticipantCreate(
                player_id=players[1].id, team_id=2, outcome={"rank": 2}
            ),  # 1500 -> 2nd
            MatchParticipantCreate(
                player_id=players[2].id, team_id=3, outcome={"rank": 3}
            ),  # 1450 -> 3rd
            MatchParticipantCreate(
                player_id=players[3].id, team_id=4, outcome={"rank": 4}
            ),  # 1400 -> 4th
        ],
    )
    await match_service.process_new_match(db=db_session, match_in=match_in)

    # 3. ASSERT: Verify the new ratings.
    new_ratings = {}
    for profile in profiles:
        await db_session.refresh(profile)
        new_ratings[profile.player_id] = profile.rating_info["rating"]

    # The highest-rated player won, so their rating MUST increase.
    # The current "draw" logic will incorrectly make it decrease.
    assert (
        new_ratings[players[0].id] > initial_ratings[0]
    ), "1st place finisher's rating should increase, even if they were the favorite"

    # The lowest-rated player lost, so their rating MUST decrease.
    assert (
        new_ratings[players[3].id] < initial_ratings[3]
    ), "4th place finisher's rating should decrease"

    # The 2nd place player should have a better rating change than the 3rd place player.
    change_p2 = new_ratings[players[1].id] - initial_ratings[1]
    change_p3 = new_ratings[players[2].id] - initial_ratings[2]
    assert (
        change_p2 > change_p3
    ), "2nd place should have a better rating change than 3rd"
