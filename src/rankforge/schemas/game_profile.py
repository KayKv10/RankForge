# src/rankforge/schemas/game_profile.py

"""Pydantic schemas for the GameProfile resource.

GameProfiles store a player's rating and stats for a specific game.
These schemas are primarily used for leaderboard and stats endpoints.
"""

from pydantic import BaseModel, ConfigDict

from .common import RatingInfo
from .player import PlayerRead


class GameProfileRead(BaseModel):
    """Properties to return for a game profile (leaderboard, player stats)."""

    id: int
    player_id: int
    game_id: int

    # Rating information with validation
    rating_info: RatingInfo

    # Flexible stats blob (wins, losses, win_rate, etc.)
    stats: dict

    # Optionally include the full player object
    player: PlayerRead | None = None

    model_config = ConfigDict(from_attributes=True)


class GameProfileWithPlayer(GameProfileRead):
    """GameProfile that always includes the player object (for leaderboards)."""

    player: PlayerRead

    model_config = ConfigDict(from_attributes=True)
