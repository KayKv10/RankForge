# tests/test_api_players.py

"""Tests for the Player API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_player(async_client: AsyncClient):
    """Test creating a new player via the POST /players/ endpoint."""
    # 1. Define the data for the new player.
    player_payload = {"name": "PlayerOne"}

    # 2. Make the API call to create the player.
    response = await async_client.post("/players/", json=player_payload)

    # 3. Assert that the response is what we expect for a successful creation.
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == player_payload["name"]
    assert "id" in data
    assert isinstance(data["id"], int)

    # The `created_at` field should also be present in the response
    assert "created_at" in data


@pytest.mark.asyncio
async def test_read_player(async_client: AsyncClient):
    """Test retrieving a single player by their ID."""
    # 1. Create a player to ensure there's data to fetch.
    player_payload = {"name": "PlayerToRead"}
    create_response = await async_client.post("/players/", json=player_payload)
    assert create_response.status_code == 201
    player_id = create_response.json()["id"]

    # 2. Try to fetch the player using their ID.
    read_response = await async_client.get(f"/players/{player_id}")

    # 3. Assert the request was successful and the data is correct.
    assert read_response.status_code == 200
    data = read_response.json()
    assert data["id"] == player_id
    assert data["name"] == player_payload["name"]


@pytest.mark.asyncio
async def test_list_players(async_client: AsyncClient):
    """Test retrieving a list of all players."""
    # 1. Create a couple of players to ensure the list is populated.
    await async_client.post("/players/", json={"name": "Alice"})
    await async_client.post("/players/", json={"name": "Bob"})

    # 2. Make the call to the list endpoint.
    response = await async_client.get("/players/")

    # 3. Assert the request was successful and the data format is correct.
    assert response.status_code == 200
    data = response.json()

    # Assert that we got a paginated response containing the players.
    assert "items" in data
    assert "total" in data
    assert "has_more" in data
    assert len(data["items"]) >= 2

    # Verify that the names of the created players are in the response list.
    response_names = {player["name"] for player in data["items"]}
    assert "Alice" in response_names
    assert "Bob" in response_names


@pytest.mark.asyncio
async def test_update_player(async_client: AsyncClient):
    """Test updating an existing player's name."""
    # 1. Create a player to update.
    original_payload = {"name": "Charlie_Old"}
    create_response = await async_client.post("/players/", json=original_payload)
    assert create_response.status_code == 201
    player_id = create_response.json()["id"]
    original_name = create_response.json()["name"]

    # 2. Define the update payload.
    update_payload = {"name": "Charlie_New"}

    # 3. Make the API call to update the player.
    update_response = await async_client.put(
        f"/players/{player_id}", json=update_payload
    )

    # 4. Assert that the update was successful.
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["id"] == player_id
    assert data["name"] == update_payload["name"]
    assert data["name"] != original_name


@pytest.mark.asyncio
async def test_delete_player(async_client: AsyncClient):
    """Test deleting a player."""
    # 1. Create a player to delete.
    payload = {"name": "PlayerToDelete"}
    create_response = await async_client.post("/players/", json=payload)
    assert create_response.status_code == 201
    player_id = create_response.json()["id"]

    # 2. Make the API call to delete the player.
    delete_response = await async_client.delete(f"/players/{player_id}")

    # 3. Assert that the delete request was successful (204 No Content).
    assert delete_response.status_code == 204

    # 4. Verify that the player is gone by trying to fetch them again.
    get_response = await async_client.get(f"/players/{player_id}")
    assert get_response.status_code == 404
