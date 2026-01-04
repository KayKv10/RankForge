# tests/test_concurrent_operations.py

"""Tests for rapid sequential operations and state consistency.

Note: True concurrency testing with shared database sessions is not possible
in this test setup. These tests verify that rapid sequential operations
maintain data consistency.
"""

import pytest
from httpx import AsyncClient

# =============================================================================
# Helper Functions
# =============================================================================


async def create_game(client: AsyncClient, name: str) -> int:
    """Helper to create a game and return its ID."""
    res = await client.post(
        "/games/", json={"name": name, "rating_strategy": "glicko2"}
    )
    assert res.status_code == 201
    return int(res.json()["id"])


async def create_player(client: AsyncClient, name: str) -> int:
    """Helper to create a player and return its ID."""
    res = await client.post("/players/", json={"name": name})
    assert res.status_code == 201
    return int(res.json()["id"])


async def create_match(
    client: AsyncClient, game_id: int, player1_id: int, player2_id: int
) -> dict:
    """Helper to create a match and return full response."""
    res = await client.post(
        "/matches/",
        json={
            "game_id": game_id,
            "participants": [
                {"player_id": player1_id, "team_id": 1, "outcome": {"result": "win"}},
                {"player_id": player2_id, "team_id": 2, "outcome": {"result": "loss"}},
            ],
        },
    )
    return {
        "status": res.status_code,
        "data": res.json() if res.status_code == 201 else None,
    }


# =============================================================================
# Rapid Sequential Operation Tests
# =============================================================================


@pytest.mark.asyncio
async def test_rapid_matches_for_same_player(async_client: AsyncClient):
    """Test that multiple matches can be created rapidly for the same player."""
    # 1. ARRANGE: Create a game and multiple players.
    game_id = await create_game(async_client, "RapidMatchGame")
    player1_id = await create_player(async_client, "RapidP1")
    player2_id = await create_player(async_client, "RapidP2")
    player3_id = await create_player(async_client, "RapidP3")
    player4_id = await create_player(async_client, "RapidP4")

    # 2. ACT: Create multiple matches in rapid succession (player1 in all matches).
    result1 = await create_match(async_client, game_id, player1_id, player2_id)
    result2 = await create_match(async_client, game_id, player1_id, player3_id)
    result3 = await create_match(async_client, game_id, player1_id, player4_id)

    # 3. ASSERT: All matches should be created successfully.
    assert result1["status"] == 201
    assert result2["status"] == 201
    assert result3["status"] == 201


@pytest.mark.asyncio
async def test_game_profile_creation_on_first_match(async_client: AsyncClient):
    """Test that GameProfiles are created correctly on first match."""
    # 1. ARRANGE: Create a game and two players (no prior matches/profiles).
    game_id = await create_game(async_client, "ProfileCreationGame")
    player1_id = await create_player(async_client, "ProfileP1")
    player2_id = await create_player(async_client, "ProfileP2")

    # 2. ACT: Create a single match to establish profiles.
    result = await create_match(async_client, game_id, player1_id, player2_id)

    # 3. ASSERT: Match should be created and profiles should exist.
    assert result["status"] == 201

    # Check leaderboard shows both players
    leaderboard_res = await async_client.get(f"/games/{game_id}/leaderboard")
    assert leaderboard_res.status_code == 200
    entries = leaderboard_res.json()["items"]

    player_ids_in_leaderboard = {e["player"]["id"] for e in entries}
    assert player1_id in player_ids_in_leaderboard
    assert player2_id in player_ids_in_leaderboard


@pytest.mark.asyncio
async def test_rating_updates_across_multiple_matches(async_client: AsyncClient):
    """Test that ratings update correctly across multiple matches."""
    # 1. ARRANGE: Create a game and players.
    game_id = await create_game(async_client, "RatingUpdateGame")
    player1_id = await create_player(async_client, "RatingUpdateP1")
    player2_id = await create_player(async_client, "RatingUpdateP2")
    player3_id = await create_player(async_client, "RatingUpdateP3")

    # 2. ACT: Create sequential matches.
    await create_match(async_client, game_id, player1_id, player2_id)
    await create_match(async_client, game_id, player2_id, player3_id)

    # 3. ASSERT: Check that final ratings are consistent.
    leaderboard_res = await async_client.get(f"/games/{game_id}/leaderboard")
    assert leaderboard_res.status_code == 200
    entries = leaderboard_res.json()["items"]

    # All three players should be in leaderboard
    assert len(entries) == 3

    # Verify ratings are different (not all still at 1500)
    ratings = [e["rating_info"]["rating"] for e in entries]
    unique_ratings = set(ratings)
    # Should have at least 2 different ratings (winners vs losers)
    assert len(unique_ratings) >= 2


@pytest.mark.asyncio
async def test_no_duplicate_unknown_player_created(async_client: AsyncClient):
    """Test that multiple matches with null player_id use the same Unknown player."""
    # 1. ARRANGE: Create a game.
    game_id = await create_game(async_client, "UnknownDuplicateGame")
    known_player1 = await create_player(async_client, "KnownDupP1")
    known_player2 = await create_player(async_client, "KnownDupP2")

    # 2. ACT: Create multiple matches with unknown players sequentially.
    match1_payload = {
        "game_id": game_id,
        "participants": [
            {"player_id": known_player1, "team_id": 1, "outcome": {"result": "win"}},
            {"player_id": None, "team_id": 2, "outcome": {"result": "loss"}},
        ],
    }
    match2_payload = {
        "game_id": game_id,
        "participants": [
            {"player_id": known_player2, "team_id": 1, "outcome": {"result": "win"}},
            {"player_id": None, "team_id": 2, "outcome": {"result": "loss"}},
        ],
    }

    res1 = await async_client.post("/matches/", json=match1_payload)
    res2 = await async_client.post("/matches/", json=match2_payload)

    # 3. ASSERT: Both matches should succeed.
    assert res1.status_code == 201
    assert res2.status_code == 201

    # Get the Unknown player IDs from both matches
    match1_unknown = next(
        p for p in res1.json()["participants"] if p["player"]["name"] == "Unknown"
    )
    match2_unknown = next(
        p for p in res2.json()["participants"] if p["player"]["name"] == "Unknown"
    )

    # Both should reference the same Unknown player ID
    assert match1_unknown["player"]["id"] == match2_unknown["player"]["id"]


@pytest.mark.asyncio
async def test_rapid_player_creation(async_client: AsyncClient):
    """Test that multiple players can be created in rapid succession."""
    # Create multiple players rapidly
    player_ids = []
    for i in range(5):
        player_id = await create_player(async_client, f"RapidCreatePlayer_{i}")
        player_ids.append(player_id)

    # All players should have unique IDs
    assert len(set(player_ids)) == 5


@pytest.mark.asyncio
async def test_rapid_game_creation(async_client: AsyncClient):
    """Test that multiple games can be created in rapid succession."""
    # Create multiple games rapidly
    game_ids = []
    for i in range(5):
        game_id = await create_game(async_client, f"RapidCreateGame_{i}")
        game_ids.append(game_id)

    # All games should have unique IDs
    assert len(set(game_ids)) == 5


@pytest.mark.asyncio
async def test_match_retrieval_immediately_after_creation(async_client: AsyncClient):
    """Test that match retrieval works correctly immediately after creation."""
    # 1. ARRANGE: Create game and players.
    game_id = await create_game(async_client, "ImmediateRetrievalGame")
    player1_id = await create_player(async_client, "ImmediateRetrievalP1")
    player2_id = await create_player(async_client, "ImmediateRetrievalP2")

    # 2. ACT: Create a match and immediately try to retrieve it.
    create_res = await async_client.post(
        "/matches/",
        json={
            "game_id": game_id,
            "participants": [
                {"player_id": player1_id, "team_id": 1, "outcome": {"result": "win"}},
                {"player_id": player2_id, "team_id": 2, "outcome": {"result": "loss"}},
            ],
        },
    )
    assert create_res.status_code == 201
    match_id = create_res.json()["id"]

    # 3. ASSERT: Immediate retrieval should work.
    get_res = await async_client.get(f"/matches/{match_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == match_id


@pytest.mark.asyncio
async def test_leaderboard_consistency_after_multiple_matches(
    async_client: AsyncClient,
):
    """Test that leaderboard remains consistent after multiple rapid matches."""
    # 1. ARRANGE: Create game and players.
    game_id = await create_game(async_client, "LeaderboardConsistGame")
    player1_id = await create_player(async_client, "LeaderboardP1")
    player2_id = await create_player(async_client, "LeaderboardP2")

    # 2. ACT: Create multiple sequential matches.
    for _ in range(3):
        res = await async_client.post(
            "/matches/",
            json={
                "game_id": game_id,
                "participants": [
                    {
                        "player_id": player1_id,
                        "team_id": 1,
                        "outcome": {"result": "win"},
                    },
                    {
                        "player_id": player2_id,
                        "team_id": 2,
                        "outcome": {"result": "loss"},
                    },
                ],
            },
        )
        assert res.status_code == 201

    # 3. ASSERT: Leaderboard should show correct order.
    leaderboard_res = await async_client.get(f"/games/{game_id}/leaderboard")
    assert leaderboard_res.status_code == 200
    entries = leaderboard_res.json()["items"]

    # Player1 (3 wins) should have highest rating
    player1_entry = next(e for e in entries if e["player"]["id"] == player1_id)
    player2_entry = next(e for e in entries if e["player"]["id"] == player2_id)

    assert (
        player1_entry["rating_info"]["rating"] > player2_entry["rating_info"]["rating"]
    )
    # Rankings should be ordered
    assert player1_entry["rank"] < player2_entry["rank"]
