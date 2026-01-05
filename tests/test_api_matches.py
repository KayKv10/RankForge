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

    # 2. CREATE two distinct 1v1 matches to ensure the list endpoint works.
    #    Each match requires at least 2 participants on different teams.
    match1_payload = {
        "game_id": game_id,
        "participants": [
            {"player_id": player_c_id, "team_id": 1, "outcome": {"result": "win"}},
            {"player_id": player_d_id, "team_id": 2, "outcome": {"result": "loss"}},
        ],
    }
    match1_res = await async_client.post("/matches/", json=match1_payload)
    assert match1_res.status_code == 201
    match1_id = match1_res.json()["id"]

    match2_payload = {
        "game_id": game_id,
        "match_metadata": {"notes": "Second match"},
        "participants": [
            {"player_id": player_d_id, "team_id": 1, "outcome": {"result": "win"}},
            {"player_id": player_c_id, "team_id": 2, "outcome": {"result": "loss"}},
        ],
    }
    match2_res = await async_client.post("/matches/", json=match2_payload)
    assert match2_res.status_code == 201
    match2_id = match2_res.json()["id"]

    # 3. EXECUTE: Make the call to the list endpoint.
    response = await async_client.get("/matches/")

    # 4. ASSERT the request was successful and the data format is correct.
    assert response.status_code == 200
    data = response.json()

    # Assert that we got a paginated response containing the matches.
    assert "items" in data
    assert "total" in data
    assert "has_more" in data
    matches_list = data["items"]
    assert len(matches_list) >= 2

    # Find our created matches in the response list
    match1_data = next((m for m in matches_list if m["id"] == match1_id), None)
    match2_data = next((m for m in matches_list if m["id"] == match2_id), None)

    # Assert that both matches were found and their data is correct
    assert match1_data is not None
    assert match1_data["game_id"] == game_id
    participant_ids_1 = {p["player"]["id"] for p in match1_data["participants"]}
    assert player_c_id in participant_ids_1

    assert match2_data is not None
    assert match2_data["match_metadata"] == {"notes": "Second match"}
    participant_ids_2 = {p["player"]["id"] for p in match2_data["participants"]}
    assert player_d_id in participant_ids_2


@pytest.mark.asyncio
async def test_delete_match(async_client: AsyncClient):
    """Test deleting a match."""
    # 1. SETUP: Create a game, players, and a 1v1 match to delete.
    game_res = await async_client.post(
        "/games/", json={"name": "DeleteTestGame", "rating_strategy": "glicko2"}
    )
    game_id = game_res.json()["id"]

    player1_res = await async_client.post("/players/", json={"name": "Player E"})
    player1_id = player1_res.json()["id"]

    player2_res = await async_client.post("/players/", json={"name": "Player F2"})
    player2_id = player2_res.json()["id"]

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

    # 2. EXECUTE: Make the API call to delete the match.
    delete_response = await async_client.delete(f"/matches/{match_id}")

    # 3. ASSERT that the delete request was successful.
    assert delete_response.status_code == 204

    # 4. VERIFY that the match is gone.
    get_response = await async_client.get(f"/matches/{match_id}")
    assert get_response.status_code == 404


# =============================================================================
# Match Metadata Edge Cases
# =============================================================================


@pytest.mark.asyncio
async def test_match_metadata_empty_dict(async_client: AsyncClient):
    """Test that matches work correctly with explicit empty metadata dict."""
    # Setup
    game_res = await async_client.post(
        "/games/", json={"name": "EmptyMetaGame", "rating_strategy": "glicko2"}
    )
    game_id = game_res.json()["id"]
    p1_res = await async_client.post("/players/", json={"name": "EmptyMetaP1"})
    p2_res = await async_client.post("/players/", json={"name": "EmptyMetaP2"})

    # Create match with explicit empty metadata
    response = await async_client.post(
        "/matches/",
        json={
            "game_id": game_id,
            "match_metadata": {},
            "participants": [
                {
                    "player_id": p1_res.json()["id"],
                    "team_id": 1,
                    "outcome": {"result": "win"},
                },
                {
                    "player_id": p2_res.json()["id"],
                    "team_id": 2,
                    "outcome": {"result": "loss"},
                },
            ],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["match_metadata"] == {}


@pytest.mark.asyncio
async def test_match_metadata_omitted(async_client: AsyncClient):
    """Test that matches work when metadata is not provided (uses default)."""
    # Setup
    game_res = await async_client.post(
        "/games/", json={"name": "NoMetaGame", "rating_strategy": "glicko2"}
    )
    game_id = game_res.json()["id"]
    p1_res = await async_client.post("/players/", json={"name": "NoMetaP1"})
    p2_res = await async_client.post("/players/", json={"name": "NoMetaP2"})

    # Create match WITHOUT metadata field
    response = await async_client.post(
        "/matches/",
        json={
            "game_id": game_id,
            # match_metadata intentionally omitted
            "participants": [
                {
                    "player_id": p1_res.json()["id"],
                    "team_id": 1,
                    "outcome": {"result": "win"},
                },
                {
                    "player_id": p2_res.json()["id"],
                    "team_id": 2,
                    "outcome": {"result": "loss"},
                },
            ],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["match_metadata"] == {}  # Default empty dict


@pytest.mark.asyncio
async def test_match_metadata_complex_structure(async_client: AsyncClient):
    """Test that metadata supports nested structures and various data types."""
    # Setup
    game_res = await async_client.post(
        "/games/", json={"name": "ComplexMetaGame", "rating_strategy": "glicko2"}
    )
    game_id = game_res.json()["id"]
    p1_res = await async_client.post("/players/", json={"name": "ComplexMetaP1"})
    p2_res = await async_client.post("/players/", json={"name": "ComplexMetaP2"})

    complex_metadata = {
        "map": "Castle Arena",
        "game_length_seconds": 342,
        "is_tournament": True,
        "scores": [21, 18],
        "settings": {
            "difficulty": "hard",
            "modifiers": ["no_items", "fast_spawn"],
        },
        "null_field": None,
    }

    response = await async_client.post(
        "/matches/",
        json={
            "game_id": game_id,
            "match_metadata": complex_metadata,
            "participants": [
                {
                    "player_id": p1_res.json()["id"],
                    "team_id": 1,
                    "outcome": {"result": "win"},
                },
                {
                    "player_id": p2_res.json()["id"],
                    "team_id": 2,
                    "outcome": {"result": "loss"},
                },
            ],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["match_metadata"]["map"] == "Castle Arena"
    assert data["match_metadata"]["game_length_seconds"] == 342
    assert data["match_metadata"]["is_tournament"] is True
    assert data["match_metadata"]["scores"] == [21, 18]
    assert data["match_metadata"]["settings"]["difficulty"] == "hard"
    assert data["match_metadata"]["null_field"] is None


@pytest.mark.asyncio
async def test_match_metadata_special_characters(async_client: AsyncClient):
    """Test that metadata handles special characters and unicode."""
    # Setup
    game_res = await async_client.post(
        "/games/", json={"name": "UnicodeMetaGame", "rating_strategy": "glicko2"}
    )
    game_id = game_res.json()["id"]
    p1_res = await async_client.post("/players/", json={"name": "UnicodeMetaP1"})
    p2_res = await async_client.post("/players/", json={"name": "UnicodeMetaP2"})

    unicode_metadata = {
        "venue": "Tokyo Arena - \u6771\u4eac",
        "player_comment": "Great game!",
        "special_chars": 'quotes: "test", backslash: \\',
    }

    response = await async_client.post(
        "/matches/",
        json={
            "game_id": game_id,
            "match_metadata": unicode_metadata,
            "participants": [
                {
                    "player_id": p1_res.json()["id"],
                    "team_id": 1,
                    "outcome": {"result": "win"},
                },
                {
                    "player_id": p2_res.json()["id"],
                    "team_id": 2,
                    "outcome": {"result": "loss"},
                },
            ],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert "\u6771\u4eac" in data["match_metadata"]["venue"]  # Japanese chars
    assert data["match_metadata"]["special_chars"] == 'quotes: "test", backslash: \\'
