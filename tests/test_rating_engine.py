# tests/test_rating_engine.py

"""Unit tests for the rating engine logic."""
from dataclasses import dataclass
from typing import Any, cast

import pytest
from rankforge.db.models import Match
from rankforge.rating.glicko2_engine import _calculate_player_scores


# Use simple dataclasses to mock the necessary SQLAlchemy model attributes
@dataclass
class MockParticipant:
    player_id: int
    team_id: int
    outcome: dict[str, Any]


@dataclass
class MockMatch:
    participants: list[MockParticipant]


def test_calculate_player_scores_for_ranked_teams():
    """
    Verify score normalization is based on the number of TEAMS, not players.
    """
    # 1. ARRANGE: An 8-player, 4-team match where teams are ranked 1st to 4th.
    match = MockMatch(
        participants=[
            # Team 1 (Rank 4)
            MockParticipant(player_id=1, team_id=1, outcome={"rank": 4}),
            MockParticipant(player_id=2, team_id=1, outcome={"rank": 4}),
            # Team 2 (Rank 3)
            MockParticipant(player_id=3, team_id=2, outcome={"rank": 3}),
            MockParticipant(player_id=4, team_id=2, outcome={"rank": 3}),
            # Team 3 (Rank 2)
            MockParticipant(player_id=5, team_id=3, outcome={"rank": 2}),
            MockParticipant(player_id=6, team_id=3, outcome={"rank": 2}),
            # Team 4 (Rank 1)
            MockParticipant(player_id=7, team_id=4, outcome={"rank": 1}),
            MockParticipant(player_id=8, team_id=4, outcome={"rank": 1}),
        ]
    )

    # 2. ACT: Call the function under test.
    scores = _calculate_player_scores(cast(Match, match))

    # 3. ASSERT: The scores should be normalized based on 4 teams (3 opponents).
    # Score = (NumOpponentTeams - (Rank - 1)) / NumOpponentTeams
    # Rank 1: (3 - 0) / 3 = 1.0
    # Rank 2: (3 - 1) / 3 = 0.666...
    # Rank 3: (3 - 2) / 3 = 0.333...
    # Rank 4: (3 - 3) / 3 = 0.0

    # Assert scores for the 1st place team (players 7, 8)
    assert scores[7] == pytest.approx(1.0)
    assert scores[8] == pytest.approx(1.0)

    # Assert scores for the 2nd place team (players 5, 6)
    assert scores[5] == pytest.approx(2.0 / 3.0)
    assert scores[6] == pytest.approx(2.0 / 3.0)

    # Assert scores for the 3rd place team (players 3, 4)
    assert scores[3] == pytest.approx(1.0 / 3.0)
    assert scores[4] == pytest.approx(1.0 / 3.0)

    # Assert scores for the 4th place team (players 1, 2)
    assert scores[1] == pytest.approx(0.0)
    assert scores[2] == pytest.approx(0.0)
