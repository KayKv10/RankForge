# tests/test_api_games.py
"""Tests for the Game API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_game(async_client: AsyncClient):
    """Test creating a new game via the POST /games/ endpoint."""
    # 1. Real-World Example: Create the data for a new game.
    description = (
        "A popular geography game where players guess locations "
        "from street view imagery."
    )
    game_payload = {
        "name": "Geoguessr",
        "rating_strategy": "glicko2",
        "description": description,
    }

    # 2. Make the API call to create the game.
    response = await async_client.post("/games/", json=game_payload)

    # 3. Assert that the response is what we expect for a successful creation.
    #    - The status code should be 201 Created.
    #    - The returned JSON should match the payload and include a database ID.
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == game_payload["name"]
    assert data["rating_strategy"] == game_payload["rating_strategy"]
    assert data["description"] == game_payload["description"]
    assert "id" in data
    assert isinstance(data["id"], int)


@pytest.mark.asyncio
async def test_read_game(async_client: AsyncClient):
    """Test retrieving a single game by its ID."""
    # 1. Create a game to ensure there's data to fetch.
    game_payload = {
        "name": "Codenames",
        "rating_strategy": "glicko2",
        "description": "A word association game for two teams.",
    }
    create_response = await async_client.post("/games/", json=game_payload)
    assert create_response.status_code == 201
    game_id = create_response.json()["id"]

    # 2. Now, try to fetch the game using its ID.
    read_response = await async_client.get(f"/games/{game_id}")

    # 3. Assert the request was successful and the data is correct.
    assert read_response.status_code == 200
    data = read_response.json()
    assert data["id"] == game_id
    assert data["name"] == game_payload["name"]
    assert data["description"] == game_payload["description"]


@pytest.mark.asyncio
async def test_list_games(async_client: AsyncClient):
    """Test retrieving a list of all games."""
    # 1. Create two distinct games to ensure the list endpoint works
    #    with multiple items.
    game1_payload = {"name": "Air Hockey", "rating_strategy": "glicko2"}
    game2_payload = {
        "name": "Golf With Friends",
        "rating_strategy": "dummy",
    }

    await async_client.post("/games/", json=game1_payload)
    await async_client.post("/games/", json=game2_payload)

    # 2. Make the call to the list endpoint.
    response = await async_client.get("/games/")

    # 3. Assert the request was successful and the data is correct.
    assert response.status_code == 200
    data = response.json()

    # Assert that we got a paginated response containing the two games.
    assert "items" in data
    assert "total" in data
    assert "has_more" in data
    assert len(data["items"]) >= 2

    # Check that the names of created games are in the response list.
    response_names = {game["name"] for game in data["items"]}
    assert game1_payload["name"] in response_names
    assert game2_payload["name"] in response_names


@pytest.mark.asyncio
async def test_update_game(async_client: AsyncClient):
    """Test updating an existing game."""
    # 1. Define  a game to update.
    original_payload = {
        "name": "Padel",
        "rating_strategy": "glicko2",
        "description": "A classic two-player padel ball game.",
    }
    create_response = await async_client.post("/games/", json=original_payload)
    assert create_response.status_code == 201
    game_id = create_response.json()["id"]

    # 2. Define the update payload, with only change in the description.
    update_payload = {
        "description": "A fast-paced, classic two-player paddle ball game."
    }

    # 3. Make the API call to update the game.
    update_response = await async_client.put(f"/games/{game_id}", json=update_payload)

    # 4. Assert that the update was successful and the data was returned.
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["id"] == game_id

    # Name should be unchanged
    assert data["name"] == original_payload["name"]

    # Description should be updated
    assert data["description"] == update_payload["description"]

    # 5. Fetch the game again to confirm the change persisted.
    get_response = await async_client.get(f"/games/{game_id}")
    assert get_response.status_code == 200
    assert get_response.json()["description"] == update_payload["description"]


@pytest.mark.asyncio
async def test_delete_game(async_client: AsyncClient):
    """Test deleting a game."""
    # 1. Create a game to delete.
    payload = {"name": "Temporary Game", "rating_strategy": "dummy"}
    create_response = await async_client.post("/games/", json=payload)
    assert create_response.status_code == 201
    game_id = create_response.json()["id"]

    # 2. Make the API call to delete the game.
    delete_response = await async_client.delete(f"/games/{game_id}")

    # 3. Assert that the delete request was successful.
    #    A successful DELETE operation often returns a 204 No Content status.
    assert delete_response.status_code == 204

    # 4. Verify that the game is actually gone.
    #    A GET request for the same ID should now return a 404.
    get_response = await async_client.get(f"/games/{game_id}")
    assert get_response.status_code == 404
