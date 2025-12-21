# tests/test_api_matches.py
"""Tests for the Match API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_match(async_client: AsyncClient):
    """Test creating a new match with participants."""
    # 1. SETUP: Create a game and two players that will participate in the match.
    game_res = await async_client.post(
        "/games/", json={"name": "Geoguessr", "rating_strategy": "glicko2"}
    )
    assert game_res.status_code == 201
    game_id = game_res.json()["id"]

    player1_res = await async_client.post("/players/", json={"name": "Alice"})
    assert player1_res.status_code == 201
    player1_id = player1_res.json()["id"]

    player2_res = await async_client.post("/players/", json={"name": "Bob"})
    assert player2_res.status_code == 201
    player2_id = player2_res.json()["id"]

    # 2. DEFINE PAYLOAD: Construct the nested payload for the new match.
    match_payload = {
        "game_id": game_id,
        "match_metadata": {"map": "A Diverse World"},
        "participants": [
            {
                "player_id": player1_id,
                "team_id": 1,
                "outcome": {"result": "win", "score": 24150},
            },
            {
                "player_id": player2_id,
                "team_id": 2,
                "outcome": {"result": "loss", "score": 19870},
            },
        ],
    }

    # 3. EXECUTE: Make the API call to create the match.
    response = await async_client.post("/matches/", json=match_payload)

    # 4. ASSERT: Check for a successful creation and verify the nested data.
    assert response.status_code == 201

    data = response.json()
    assert data["game_id"] == game_id
    assert data["match_metadata"]["map"] == "A Diverse World"
    assert "id" in data
    assert "played_at" in data

    # Assertions for the nested participants
    assert len(data["participants"]) == 2
    participant_pids = {p["player"]["id"] for p in data["participants"]}
    assert player1_id in participant_pids
    assert player2_id in participant_pids

    # Check that the participants' outcome is correct
    alice_data = next(
        p for p in data["participants"] if p["player"]["id"] == player1_id
    )
    assert alice_data["outcome"]["result"] == "win"
    assert alice_data["outcome"]["score"] == 24150

    bob_data = next(p for p in data["participants"] if p["player"]["id"] == player2_id)
    assert bob_data["outcome"]["result"] == "loss"
    assert bob_data["outcome"]["score"] == 19870


@pytest.mark.asyncio
async def test_read_match(async_client: AsyncClient):
    """Test retrieving a single match by its ID."""
    # 1. SETUP: Create a game and players.
    game_res = await async_client.post(
        "/games/", json={"name": "TestGame", "rating_strategy": "glicko2"}
    )
    game_id = game_res.json()["id"]

    player1_res = await async_client.post("/players/", json={"name": "Player A"})
    player1_id = player1_res.json()["id"]

    player2_res = await async_client.post("/players/", json={"name": "Player B"})
    player2_id = player2_res.json()["id"]

    # 2. CREATE a match to fetch.
    match_payload = {
        "game_id": game_id,
        "participants": [
            {"player_id": player1_id, "team_id": 1, "outcome": {"result": "win"}},
            {"player_id": player2_id, "team_id": 2, "outcome": {"result": "loss"}},
        ],
    }
    create_response = await async_client.post("/matches/", json=match_payload)
    assert create_response.status_code == 201
    match_id = create_response.json()["id"]

    # 3. EXECUTE: Try to fetch the match using its ID.
    read_response = await async_client.get(f"/matches/{match_id}")

    # 4. ASSERT the request was successful and the nested data is correct.
    assert read_response.status_code == 200
    data = read_response.json()

    assert data["id"] == match_id
    assert data["game_id"] == game_id
    assert len(data["participants"]) == 2

    # Sort participants by player ID for deterministic checks
    sorted_participants = sorted(data["participants"], key=lambda p: p["player"]["id"])

    # Assertions for the first participant (Player A)
    p1_data = sorted_participants[0]
    assert p1_data["player"]["id"] == player1_id
    assert p1_data["player"]["name"] == "Player A"
    assert p1_data["team_id"] == 1
    assert p1_data["outcome"] == {"result": "win"}

    # Assertions for the second participant (Player B)
    p2_data = sorted_participants[1]
    assert p2_data["player"]["id"] == player2_id
    assert p2_data["player"]["name"] == "Player B"
    assert p2_data["team_id"] == 2
    assert p2_data["outcome"] == {"result": "loss"}


@pytest.mark.asyncio
async def test_list_matches(async_client: AsyncClient):
    """Test retrieving a list of all matches."""
    # 1. SETUP: Create a game and multiple players for different matches.
    game_res = await async_client.post(
        "/games/", json={"name": "ListTestGame", "rating_strategy": "glicko2"}
    )
    game_id = game_res.json()["id"]

    player_c_res = await async_client.post("/players/", json={"name": "Player C"})
    player_c_id = player_c_res.json()["id"]

    player_d_res = await async_client.post("/players/", json={"name": "Player D"})
    player_d_id = player_d_res.json()["id"]

    # 2. CREATE two distinct matches to ensure the list endpoint works.
    match1_payload = {
        "game_id": game_id,
        "participants": [
            {"player_id": player_c_id, "team_id": 1, "outcome": {"result": "win"}}
        ],
    }
    match1_res = await async_client.post("/matches/", json=match1_payload)
    assert match1_res.status_code == 201
    match1_id = match1_res.json()["id"]

    match2_payload = {
        "game_id": game_id,
        "match_metadata": {"notes": "Second match"},
        "participants": [
            {"player_id": player_d_id, "team_id": 1, "outcome": {"result": "win"}}
        ],
    }
    match2_res = await async_client.post("/matches/", json=match2_payload)
    assert match2_res.status_code == 201
    match2_id = match2_res.json()["id"]

    # 3. EXECUTE: Make the call to the list endpoint.
    response = await async_client.get("/matches/")

    # 4. ASSERT the request was successful and the data format is correct.
    assert response.status_code == 200
    matches_list = response.json()

    assert isinstance(matches_list, list)
    assert len(matches_list) >= 2

    # Find our created matches in the response list
    match1_data = next((m for m in matches_list if m["id"] == match1_id), None)
    match2_data = next((m for m in matches_list if m["id"] == match2_id), None)

    # Assert that both matches were found and their data is correct
    assert match1_data is not None
    assert match1_data["game_id"] == game_id
    assert match1_data["participants"][0]["player"]["id"] == player_c_id

    assert match2_data is not None
    assert match2_data["match_metadata"] == {"notes": "Second match"}
    assert match2_data["participants"][0]["player"]["id"] == player_d_id


@pytest.mark.asyncio
async def test_delete_match(async_client: AsyncClient):
    """Test deleting a match."""
    # 1. SETUP: Create a game, a player, and a match to delete.
    game_res = await async_client.post(
        "/games/", json={"name": "DeleteTestGame", "rating_strategy": "glicko2"}
    )
    game_id = game_res.json()["id"]
    player_res = await async_client.post("/players/", json={"name": "Player E"})
    player_id = player_res.json()["id"]

    match_payload = {
        "game_id": game_id,
        "participants": [
            {"player_id": player_id, "team_id": 1, "outcome": {"result": "win"}}
        ],
    }
    create_response = await async_client.post("/matches/", json=match_payload)
    assert create_response.status_code == 201
    match_id = create_response.json()["id"]

    # 2. EXECUTE: Make the API call to delete the match.
    delete_response = await async_client.delete(f"/matches/{match_id}")

    # 3. ASSERT that the delete request was successful.
    assert delete_response.status_code == 204

    # 4. VERIFY that the match is gone.
    get_response = await async_client.get(f"/matches/{match_id}")
    assert get_response.status_code == 404
