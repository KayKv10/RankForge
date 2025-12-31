# src/rankforge/schemas/leaderboard.py

"""Leaderboard schemas for game rankings."""

from pydantic import BaseModel, ConfigDict, Field

from .common import RatingInfo
from .player import PlayerRead


class LeaderboardEntry(BaseModel):
    """Single entry in a game leaderboard.

    Attributes:
        rank: Position in leaderboard (1-indexed)
        player: The player information
        rating_info: Current rating information (rating, rd, vol)
        stats: Player stats for this game (wins, losses, matches_played, etc.)
    """

    rank: int = Field(..., ge=1, description="Position in leaderboard (1-indexed)")
    player: PlayerRead
    rating_info: RatingInfo
    stats: dict = Field(default_factory=dict, description="Game-specific player stats")

    model_config = ConfigDict(from_attributes=True)
