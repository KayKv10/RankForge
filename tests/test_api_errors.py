# tests/test_api_errors.py

"""Tests for HTTP error responses across all API endpoints."""

import pytest
from httpx import AsyncClient

# =============================================================================
# 404 Not Found Errors - Games
# =============================================================================


@pytest.mark.asyncio
async def test_get_nonexistent_game_returns_404(async_client: AsyncClient):
    """Test that fetching a non-existent game returns 404."""
    response = await async_client.get("/games/999999")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_update_nonexistent_game_returns_404(async_client: AsyncClient):
    """Test that updating a non-existent game returns 404."""
    response = await async_client.put(
        "/games/999999", json={"name": "Updated Name", "rating_strategy": "glicko2"}
    )

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_delete_nonexistent_game_returns_404(async_client: AsyncClient):
    """Test that deleting a non-existent game returns 404."""
    response = await async_client.delete("/games/999999")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_get_leaderboard_nonexistent_game_returns_404(async_client: AsyncClient):
    """Test that getting leaderboard for non-existent game returns 404."""
    response = await async_client.get("/games/999999/leaderboard")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


# =============================================================================
# 404 Not Found Errors - Players
# =============================================================================


@pytest.mark.asyncio
async def test_get_nonexistent_player_returns_404(async_client: AsyncClient):
    """Test that fetching a non-existent player returns 404."""
    response = await async_client.get("/players/999999")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_update_nonexistent_player_returns_404(async_client: AsyncClient):
    """Test that updating a non-existent player returns 404."""
    response = await async_client.put("/players/999999", json={"name": "Updated Name"})

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_delete_nonexistent_player_returns_404(async_client: AsyncClient):
    """Test that deleting a non-existent player returns 404."""
    response = await async_client.delete("/players/999999")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_get_stats_nonexistent_player_returns_404(async_client: AsyncClient):
    """Test that getting stats for non-existent player returns 404."""
    response = await async_client.get("/players/999999/stats")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_get_matches_nonexistent_player_returns_404(async_client: AsyncClient):
    """Test that getting matches for non-existent player returns 404."""
    response = await async_client.get("/players/999999/matches")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


# =============================================================================
# 404 Not Found Errors - Matches
# =============================================================================


@pytest.mark.asyncio
async def test_get_nonexistent_match_returns_404(async_client: AsyncClient):
    """Test that fetching a non-existent match returns 404."""
    response = await async_client.get("/matches/999999")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_delete_nonexistent_match_returns_404(async_client: AsyncClient):
    """Test that deleting a non-existent match returns 404."""
    response = await async_client.delete("/matches/999999")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


# =============================================================================
# 409 Conflict Errors - Duplicate Names
# =============================================================================


@pytest.mark.asyncio
async def test_create_duplicate_game_name_returns_409(async_client: AsyncClient):
    """Test that creating a game with a duplicate name returns 409."""
    # 1. ARRANGE: Create the first game.
    game_payload = {"name": "UniqueGameName409", "rating_strategy": "glicko2"}
    first_response = await async_client.post("/games/", json=game_payload)
    assert first_response.status_code == 201

    # 2. ACT: Try to create another game with the same name.
    response = await async_client.post("/games/", json=game_payload)

    # 3. ASSERT: Should return 409 Conflict.
    assert response.status_code == 409
    data = response.json()
    assert "detail" in data
    assert "already exists" in data["detail"].lower()


@pytest.mark.asyncio
async def test_create_duplicate_player_name_returns_409(async_client: AsyncClient):
    """Test that creating a player with a duplicate name returns 409."""
    # 1. ARRANGE: Create the first player.
    player_payload = {"name": "UniquePlayerName409"}
    first_response = await async_client.post("/players/", json=player_payload)
    assert first_response.status_code == 201

    # 2. ACT: Try to create another player with the same name.
    response = await async_client.post("/players/", json=player_payload)

    # 3. ASSERT: Should return 409 Conflict.
    assert response.status_code == 409
    data = response.json()
    assert "detail" in data
    assert "already exists" in data["detail"].lower()


@pytest.mark.asyncio
async def test_update_game_to_duplicate_name_returns_409(async_client: AsyncClient):
    """Test that updating a game to a duplicate name returns 409."""
    # 1. ARRANGE: Create two games with different names.
    game1_res = await async_client.post(
        "/games/", json={"name": "OriginalGame409", "rating_strategy": "glicko2"}
    )
    assert game1_res.status_code == 201

    game2_res = await async_client.post(
        "/games/", json={"name": "TargetGame409", "rating_strategy": "glicko2"}
    )
    assert game2_res.status_code == 201
    game2_id = game2_res.json()["id"]

    # 2. ACT: Try to update game2 to have game1's name.
    response = await async_client.put(
        f"/games/{game2_id}", json={"name": "OriginalGame409"}
    )

    # 3. ASSERT: Should return 409 Conflict.
    assert response.status_code == 409
    data = response.json()
    assert "detail" in data
    assert "already exists" in data["detail"].lower()


@pytest.mark.asyncio
async def test_update_player_to_duplicate_name_returns_409(async_client: AsyncClient):
    """Test that updating a player to a duplicate name returns 409."""
    # 1. ARRANGE: Create two players with different names.
    player1_res = await async_client.post(
        "/players/", json={"name": "OriginalPlayer409"}
    )
    assert player1_res.status_code == 201

    player2_res = await async_client.post("/players/", json={"name": "TargetPlayer409"})
    assert player2_res.status_code == 201
    player2_id = player2_res.json()["id"]

    # 2. ACT: Try to update player2 to have player1's name.
    response = await async_client.put(
        f"/players/{player2_id}", json={"name": "OriginalPlayer409"}
    )

    # 3. ASSERT: Should return 409 Conflict.
    assert response.status_code == 409
    data = response.json()
    assert "detail" in data
    assert "already exists" in data["detail"].lower()


# =============================================================================
# 422 Validation Errors - Game Schema
# =============================================================================


@pytest.mark.asyncio
async def test_create_game_with_invalid_rating_strategy_returns_422(
    async_client: AsyncClient,
):
    """Test that creating a game with an invalid rating strategy returns 422."""
    response = await async_client.post(
        "/games/", json={"name": "TestGame", "rating_strategy": "invalid_strategy"}
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_game_with_empty_name_returns_422(async_client: AsyncClient):
    """Test that creating a game with an empty name returns 422."""
    response = await async_client.post(
        "/games/", json={"name": "", "rating_strategy": "glicko2"}
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_game_with_short_name_returns_422(async_client: AsyncClient):
    """Test that creating a game with a name less than 2 chars returns 422."""
    response = await async_client.post(
        "/games/", json={"name": "X", "rating_strategy": "glicko2"}
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_game_with_too_long_name_returns_422(async_client: AsyncClient):
    """Test that creating a game with a name over 200 chars returns 422."""
    long_name = "X" * 201
    response = await async_client.post(
        "/games/", json={"name": long_name, "rating_strategy": "glicko2"}
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_game_with_too_long_description_returns_422(
    async_client: AsyncClient,
):
    """Test that creating a game with a description over 1000 chars returns 422."""
    long_description = "X" * 1001
    response = await async_client.post(
        "/games/",
        json={
            "name": "ValidGame",
            "rating_strategy": "glicko2",
            "description": long_description,
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_game_without_required_fields_returns_422(
    async_client: AsyncClient,
):
    """Test that creating a game without required fields returns 422."""
    # Missing rating_strategy
    response = await async_client.post("/games/", json={"name": "TestGame"})

    assert response.status_code == 422


# =============================================================================
# 422 Validation Errors - Player Schema
# =============================================================================


@pytest.mark.asyncio
async def test_create_player_with_empty_name_returns_422(async_client: AsyncClient):
    """Test that creating a player with an empty name returns 422."""
    response = await async_client.post("/players/", json={"name": ""})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_player_with_short_name_returns_422(async_client: AsyncClient):
    """Test that creating a player with a name less than 2 chars returns 422."""
    response = await async_client.post("/players/", json={"name": "X"})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_player_with_too_long_name_returns_422(async_client: AsyncClient):
    """Test that creating a player with a name over 100 chars returns 422."""
    long_name = "X" * 101
    response = await async_client.post("/players/", json={"name": long_name})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_player_without_name_returns_422(async_client: AsyncClient):
    """Test that creating a player without a name returns 422."""
    response = await async_client.post("/players/", json={})

    assert response.status_code == 422


# =============================================================================
# 422 Validation Errors - Update Schemas
# =============================================================================


@pytest.mark.asyncio
async def test_update_game_with_invalid_rating_strategy_returns_422(
    async_client: AsyncClient,
):
    """Test that updating a game with an invalid rating strategy returns 422."""
    # 1. ARRANGE: Create a valid game first.
    game_res = await async_client.post(
        "/games/", json={"name": "GameToUpdate422", "rating_strategy": "glicko2"}
    )
    assert game_res.status_code == 201
    game_id = game_res.json()["id"]

    # 2. ACT: Try to update with invalid rating strategy.
    response = await async_client.put(
        f"/games/{game_id}", json={"rating_strategy": "invalid_strategy"}
    )

    # 3. ASSERT: Should return 422.
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_player_with_short_name_returns_422(async_client: AsyncClient):
    """Test that updating a player with a name less than 2 chars returns 422."""
    # 1. ARRANGE: Create a valid player first.
    player_res = await async_client.post(
        "/players/", json={"name": "PlayerToUpdate422"}
    )
    assert player_res.status_code == 201
    player_id = player_res.json()["id"]

    # 2. ACT: Try to update with a too-short name.
    response = await async_client.put(f"/players/{player_id}", json={"name": "X"})

    # 3. ASSERT: Should return 422.
    assert response.status_code == 422


# =============================================================================
# Path Parameter Validation Errors
# =============================================================================


@pytest.mark.asyncio
async def test_get_game_with_invalid_id_type_returns_422(async_client: AsyncClient):
    """Test that fetching a game with non-integer ID returns 422."""
    response = await async_client.get("/games/not-a-number")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_player_with_invalid_id_type_returns_422(async_client: AsyncClient):
    """Test that fetching a player with non-integer ID returns 422."""
    response = await async_client.get("/players/not-a-number")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_match_with_invalid_id_type_returns_422(async_client: AsyncClient):
    """Test that fetching a match with non-integer ID returns 422."""
    response = await async_client.get("/matches/not-a-number")

    assert response.status_code == 422


# =============================================================================
# Query Parameter Validation Errors
# =============================================================================


@pytest.mark.asyncio
async def test_list_games_with_negative_skip_returns_422(async_client: AsyncClient):
    """Test that listing games with negative skip returns 422."""
    response = await async_client.get("/games/?skip=-1")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_games_with_zero_limit_returns_422(async_client: AsyncClient):
    """Test that listing games with limit=0 returns 422."""
    response = await async_client.get("/games/?limit=0")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_games_with_excessive_limit_returns_422(async_client: AsyncClient):
    """Test that listing games with limit > 100 returns 422."""
    response = await async_client.get("/games/?limit=101")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_games_with_invalid_sort_field_returns_422(
    async_client: AsyncClient,
):
    """Test that listing games with invalid sort field returns 422."""
    response = await async_client.get("/games/?sort_by=invalid_field")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_games_with_invalid_sort_order_returns_422(
    async_client: AsyncClient,
):
    """Test that listing games with invalid sort order returns 422."""
    response = await async_client.get("/games/?sort_order=invalid_order")

    assert response.status_code == 422
