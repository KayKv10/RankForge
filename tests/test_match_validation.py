# tests/test_match_validation.py

"""Tests for match creation validation and error handling."""

import pytest
from httpx import AsyncClient

# =============================================================================
# Participant Count Validation Tests
# =============================================================================


@pytest.mark.asyncio
async def test_match_with_zero_participants_returns_422(async_client: AsyncClient):
    """Test that creating a match with zero participants returns 422."""
    # 1. ARRANGE: Create a game to reference.
    game_res = await async_client.post(
        "/games/", json={"name": "ZeroParticipantGame", "rating_strategy": "glicko2"}
    )
    assert game_res.status_code == 201
    game_id = game_res.json()["id"]

    # 2. ACT: Try to create a match with zero participants.
    match_payload = {
        "game_id": game_id,
        "participants": [],
    }
    response = await async_client.post("/matches/", json=match_payload)

    # 3. ASSERT: Should return 422 with appropriate error message.
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert "at least 2 participants" in data["detail"].lower()


@pytest.mark.asyncio
async def test_match_with_one_participant_returns_422(async_client: AsyncClient):
    """Test that creating a match with only one participant returns 422."""
    # 1. ARRANGE: Create a game and a single player.
    game_res = await async_client.post(
        "/games/", json={"name": "OneParticipantGame", "rating_strategy": "glicko2"}
    )
    assert game_res.status_code == 201
    game_id = game_res.json()["id"]

    player_res = await async_client.post("/players/", json={"name": "LonePlayer"})
    assert player_res.status_code == 201
    player_id = player_res.json()["id"]

    # 2. ACT: Try to create a match with only one participant.
    match_payload = {
        "game_id": game_id,
        "participants": [
            {"player_id": player_id, "team_id": 1, "outcome": {"result": "win"}},
        ],
    }
    response = await async_client.post("/matches/", json=match_payload)

    # 3. ASSERT: Should return 422 with appropriate error message.
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert "at least 2 participants" in data["detail"].lower()


# =============================================================================
# Duplicate Player Validation Tests
# =============================================================================


@pytest.mark.asyncio
async def test_match_with_duplicate_player_returns_422(async_client: AsyncClient):
    """Test that creating a match with duplicate player IDs returns 422."""
    # 1. ARRANGE: Create a game and a player.
    game_res = await async_client.post(
        "/games/", json={"name": "DuplicatePlayerGame", "rating_strategy": "glicko2"}
    )
    assert game_res.status_code == 201
    game_id = game_res.json()["id"]

    player_res = await async_client.post("/players/", json={"name": "DuplicateMe"})
    assert player_res.status_code == 201
    player_id = player_res.json()["id"]

    # 2. ACT: Try to create a match where the same player appears twice.
    match_payload = {
        "game_id": game_id,
        "participants": [
            {"player_id": player_id, "team_id": 1, "outcome": {"result": "win"}},
            {"player_id": player_id, "team_id": 2, "outcome": {"result": "loss"}},
        ],
    }
    response = await async_client.post("/matches/", json=match_payload)

    # 3. ASSERT: Should return 422 with duplicate player error.
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert "duplicate" in data["detail"].lower()


# =============================================================================
# Team Validation Tests
# =============================================================================


@pytest.mark.asyncio
async def test_match_with_all_same_team_returns_422(async_client: AsyncClient):
    """Test that creating a match where all players are on the same team returns 422."""
    # 1. ARRANGE: Create a game and two players.
    game_res = await async_client.post(
        "/games/", json={"name": "SameTeamGame", "rating_strategy": "glicko2"}
    )
    assert game_res.status_code == 201
    game_id = game_res.json()["id"]

    player1_res = await async_client.post("/players/", json={"name": "TeamPlayer1"})
    assert player1_res.status_code == 201
    player1_id = player1_res.json()["id"]

    player2_res = await async_client.post("/players/", json={"name": "TeamPlayer2"})
    assert player2_res.status_code == 201
    player2_id = player2_res.json()["id"]

    # 2. ACT: Try to create a match where both players are on the same team.
    match_payload = {
        "game_id": game_id,
        "participants": [
            {"player_id": player1_id, "team_id": 1, "outcome": {"result": "win"}},
            {"player_id": player2_id, "team_id": 1, "outcome": {"result": "win"}},
        ],
    }
    response = await async_client.post("/matches/", json=match_payload)

    # 3. ASSERT: Should return 422 with insufficient teams error.
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert "at least 2 teams" in data["detail"].lower()


# =============================================================================
# Resource Not Found Tests
# =============================================================================


@pytest.mark.asyncio
async def test_match_with_nonexistent_game_returns_404(async_client: AsyncClient):
    """Test that creating a match with a non-existent game ID returns 404."""
    # 1. ARRANGE: Create a player but use a fake game ID.
    player_res = await async_client.post("/players/", json={"name": "NoGamePlayer"})
    assert player_res.status_code == 201
    player_id = player_res.json()["id"]

    another_player_res = await async_client.post(
        "/players/", json={"name": "NoGamePlayer2"}
    )
    assert another_player_res.status_code == 201
    another_player_id = another_player_res.json()["id"]

    # 2. ACT: Try to create a match with a non-existent game ID.
    match_payload = {
        "game_id": 999999,  # Non-existent game
        "participants": [
            {"player_id": player_id, "team_id": 1, "outcome": {"result": "win"}},
            {
                "player_id": another_player_id,
                "team_id": 2,
                "outcome": {"result": "loss"},
            },
        ],
    }
    response = await async_client.post("/matches/", json=match_payload)

    # 3. ASSERT: Should return 404 with game not found error.
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "game" in data["detail"].lower()
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_match_with_nonexistent_player_returns_404(async_client: AsyncClient):
    """Test that creating a match with a non-existent player ID returns 404."""
    # 1. ARRANGE: Create a game and one valid player.
    game_res = await async_client.post(
        "/games/", json={"name": "MissingPlayerGame", "rating_strategy": "glicko2"}
    )
    assert game_res.status_code == 201
    game_id = game_res.json()["id"]

    player_res = await async_client.post("/players/", json={"name": "ValidPlayer"})
    assert player_res.status_code == 201
    player_id = player_res.json()["id"]

    # 2. ACT: Try to create a match with one valid and one non-existent player.
    match_payload = {
        "game_id": game_id,
        "participants": [
            {"player_id": player_id, "team_id": 1, "outcome": {"result": "win"}},
            {"player_id": 999999, "team_id": 2, "outcome": {"result": "loss"}},
        ],
    }
    response = await async_client.post("/matches/", json=match_payload)

    # 3. ASSERT: Should return 404 with player not found error.
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "player" in data["detail"].lower()
    assert "not found" in data["detail"].lower()


# =============================================================================
# Outcome Validation Tests (Pydantic validation at schema level)
# =============================================================================


@pytest.mark.asyncio
async def test_match_with_invalid_result_returns_422(async_client: AsyncClient):
    """Test that creating a match with an invalid result value returns 422."""
    # 1. ARRANGE: Create a game and two players.
    game_res = await async_client.post(
        "/games/", json={"name": "InvalidResultGame", "rating_strategy": "glicko2"}
    )
    assert game_res.status_code == 201
    game_id = game_res.json()["id"]

    player1_res = await async_client.post("/players/", json={"name": "ResultPlayer1"})
    assert player1_res.status_code == 201
    player1_id = player1_res.json()["id"]

    player2_res = await async_client.post("/players/", json={"name": "ResultPlayer2"})
    assert player2_res.status_code == 201
    player2_id = player2_res.json()["id"]

    # 2. ACT: Try to create a match with an invalid result value.
    match_payload = {
        "game_id": game_id,
        "participants": [
            {
                "player_id": player1_id,
                "team_id": 1,
                "outcome": {"result": "invalid_result"},
            },
            {"player_id": player2_id, "team_id": 2, "outcome": {"result": "loss"}},
        ],
    }
    response = await async_client.post("/matches/", json=match_payload)

    # 3. ASSERT: Should return 422 (Pydantic validation error).
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_match_with_zero_rank_returns_422(async_client: AsyncClient):
    """Test that creating a match with rank=0 returns 422 (rank must be >= 1)."""
    # 1. ARRANGE: Create a game and two players.
    game_res = await async_client.post(
        "/games/", json={"name": "ZeroRankGame", "rating_strategy": "glicko2"}
    )
    assert game_res.status_code == 201
    game_id = game_res.json()["id"]

    player1_res = await async_client.post("/players/", json={"name": "RankPlayer1"})
    assert player1_res.status_code == 201
    player1_id = player1_res.json()["id"]

    player2_res = await async_client.post("/players/", json={"name": "RankPlayer2"})
    assert player2_res.status_code == 201
    player2_id = player2_res.json()["id"]

    # 2. ACT: Try to create a match with rank=0.
    match_payload = {
        "game_id": game_id,
        "participants": [
            {"player_id": player1_id, "team_id": 1, "outcome": {"rank": 0}},
            {"player_id": player2_id, "team_id": 2, "outcome": {"rank": 1}},
        ],
    }
    response = await async_client.post("/matches/", json=match_payload)

    # 3. ASSERT: Should return 422 (Pydantic validation error for rank >= 1).
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_match_with_negative_rank_returns_422(async_client: AsyncClient):
    """Test that creating a match with negative rank returns 422."""
    # 1. ARRANGE: Create a game and two players.
    game_res = await async_client.post(
        "/games/", json={"name": "NegativeRankGame", "rating_strategy": "glicko2"}
    )
    assert game_res.status_code == 201
    game_id = game_res.json()["id"]

    player1_res = await async_client.post("/players/", json={"name": "NegRankPlayer1"})
    assert player1_res.status_code == 201
    player1_id = player1_res.json()["id"]

    player2_res = await async_client.post("/players/", json={"name": "NegRankPlayer2"})
    assert player2_res.status_code == 201
    player2_id = player2_res.json()["id"]

    # 2. ACT: Try to create a match with a negative rank.
    match_payload = {
        "game_id": game_id,
        "participants": [
            {"player_id": player1_id, "team_id": 1, "outcome": {"rank": -1}},
            {"player_id": player2_id, "team_id": 2, "outcome": {"rank": 1}},
        ],
    }
    response = await async_client.post("/matches/", json=match_payload)

    # 3. ASSERT: Should return 422 (Pydantic validation error).
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_match_with_missing_outcome_returns_422(async_client: AsyncClient):
    """Test that creating a match without an outcome field returns 422."""
    # 1. ARRANGE: Create a game and two players.
    game_res = await async_client.post(
        "/games/", json={"name": "MissingOutcomeGame", "rating_strategy": "glicko2"}
    )
    assert game_res.status_code == 201
    game_id = game_res.json()["id"]

    player1_res = await async_client.post("/players/", json={"name": "OutcomePlayer1"})
    assert player1_res.status_code == 201
    player1_id = player1_res.json()["id"]

    player2_res = await async_client.post("/players/", json={"name": "OutcomePlayer2"})
    assert player2_res.status_code == 201
    player2_id = player2_res.json()["id"]

    # 2. ACT: Try to create a match without the required outcome field.
    match_payload = {
        "game_id": game_id,
        "participants": [
            {"player_id": player1_id, "team_id": 1},  # Missing outcome
            {"player_id": player2_id, "team_id": 2, "outcome": {"result": "loss"}},
        ],
    }
    response = await async_client.post("/matches/", json=match_payload)

    # 3. ASSERT: Should return 422 (Pydantic validation error for missing field).
    assert response.status_code == 422


# =============================================================================
# Anonymous/Unknown Player Tests
# =============================================================================


@pytest.mark.asyncio
async def test_match_with_null_player_id_creates_unknown_player(
    async_client: AsyncClient,
):
    """Test that a participant with player_id=None uses the shared Unknown player."""
    # 1. ARRANGE: Create a game and one known player.
    game_res = await async_client.post(
        "/games/", json={"name": "UnknownPlayerGame", "rating_strategy": "glicko2"}
    )
    assert game_res.status_code == 201
    game_id = game_res.json()["id"]

    player_res = await async_client.post("/players/", json={"name": "KnownPlayer"})
    assert player_res.status_code == 201
    known_player_id = player_res.json()["id"]

    # 2. ACT: Create a match with one known player and one unknown (null player_id).
    match_payload = {
        "game_id": game_id,
        "participants": [
            {"player_id": known_player_id, "team_id": 1, "outcome": {"result": "win"}},
            {
                "player_id": None,
                "team_id": 2,
                "outcome": {"result": "loss"},
            },  # Unknown player
        ],
    }
    response = await async_client.post("/matches/", json=match_payload)

    # 3. ASSERT: Match should be created successfully.
    assert response.status_code == 201
    data = response.json()

    # Find the participant with the Unknown player
    unknown_participant = next(
        (p for p in data["participants"] if p["player"]["id"] != known_player_id), None
    )

    assert unknown_participant is not None
    assert unknown_participant["player"]["name"] == "Unknown"


@pytest.mark.asyncio
async def test_multiple_unknown_players_in_same_match(async_client: AsyncClient):
    """Test multiple null player_ids resolve to same Unknown player."""
    # 1. ARRANGE: Create a game.
    game_res = await async_client.post(
        "/games/", json={"name": "MultiUnknownGame", "rating_strategy": "glicko2"}
    )
    assert game_res.status_code == 201
    game_id = game_res.json()["id"]

    # 2. ACT: Create a match with multiple unknown participants on different teams.
    match_payload = {
        "game_id": game_id,
        "participants": [
            {
                "player_id": None,
                "team_id": 1,
                "outcome": {"result": "win"},
            },  # Unknown 1
            {
                "player_id": None,
                "team_id": 2,
                "outcome": {"result": "loss"},
            },  # Unknown 2
        ],
    }
    response = await async_client.post("/matches/", json=match_payload)

    # 3. ASSERT: Match should be created successfully.
    assert response.status_code == 201
    data = response.json()

    # Both participants should be the same Unknown player (shared)
    participant_ids = {p["player"]["id"] for p in data["participants"]}
    participant_names = {p["player"]["name"] for p in data["participants"]}

    # They should all have the same player ID (the shared Unknown player)
    assert len(participant_ids) == 1  # Same player used for both
    assert participant_names == {"Unknown"}


@pytest.mark.asyncio
async def test_unknown_player_exempt_from_duplicate_check(async_client: AsyncClient):
    """Test that multiple unknown players don't trigger duplicate player error."""
    # 1. ARRANGE: Create a game and one known player.
    game_res = await async_client.post(
        "/games/",
        json={"name": "UnknownDuplicateExemptGame", "rating_strategy": "glicko2"},
    )
    assert game_res.status_code == 201
    game_id = game_res.json()["id"]

    player_res = await async_client.post(
        "/players/", json={"name": "KnownPlayerForExempt"}
    )
    assert player_res.status_code == 201
    known_player_id = player_res.json()["id"]

    # 2. ACT: Create a match with one known player and two unknowns.
    #    This tests that the Unknown player can appear multiple times.
    match_payload = {
        "game_id": game_id,
        "participants": [
            {"player_id": known_player_id, "team_id": 1, "outcome": {"result": "win"}},
            {"player_id": None, "team_id": 2, "outcome": {"result": "loss"}},
            {"player_id": None, "team_id": 3, "outcome": {"result": "loss"}},
        ],
    }
    response = await async_client.post("/matches/", json=match_payload)

    # 3. ASSERT: Match created (Unknown exempt from duplicate check).
    assert response.status_code == 201
    data = response.json()
    assert len(data["participants"]) == 3

    # Verify the Unknown player appears twice
    unknown_participants = [
        p for p in data["participants"] if p["player"]["name"] == "Unknown"
    ]
    assert len(unknown_participants) == 2


# =============================================================================
# Edge Cases
# =============================================================================


@pytest.mark.asyncio
async def test_match_with_negative_team_id_returns_422(async_client: AsyncClient):
    """Test that creating a match with negative team_id returns 422."""
    # 1. ARRANGE: Create a game and two players.
    game_res = await async_client.post(
        "/games/", json={"name": "NegTeamGame", "rating_strategy": "glicko2"}
    )
    assert game_res.status_code == 201
    game_id = game_res.json()["id"]

    player1_res = await async_client.post("/players/", json={"name": "NegTeamPlayer1"})
    assert player1_res.status_code == 201
    player1_id = player1_res.json()["id"]

    player2_res = await async_client.post("/players/", json={"name": "NegTeamPlayer2"})
    assert player2_res.status_code == 201
    player2_id = player2_res.json()["id"]

    # 2. ACT: Try to create a match with a negative team_id.
    match_payload = {
        "game_id": game_id,
        "participants": [
            {"player_id": player1_id, "team_id": -1, "outcome": {"result": "win"}},
            {"player_id": player2_id, "team_id": 2, "outcome": {"result": "loss"}},
        ],
    }
    response = await async_client.post("/matches/", json=match_payload)

    # 3. ASSERT: Should return 422 (team_id >= 0 validation).
    assert response.status_code == 422
