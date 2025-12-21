# src/rankforge/schemas/__init__.py

"""Pydantic schemas for API validation and serialization."""

from .common import RatingInfo
from .game import GameBase, GameCreate, GameRead, GameUpdate, RatingStrategy
from .game_profile import GameProfileRead, GameProfileWithPlayer
from .match import (
    BinaryOutcome,
    MatchBase,
    MatchCreate,
    MatchParticipantBase,
    MatchParticipantCreate,
    MatchParticipantRead,
    MatchRead,
    Outcome,
    RankedOutcome,
)
from .player import PlayerBase, PlayerCreate, PlayerRead, PlayerUpdate

__all__ = [
    # Common
    "RatingInfo",
    # Game
    "GameBase",
    "GameCreate",
    "GameRead",
    "GameUpdate",
    "RatingStrategy",
    # Game Profile
    "GameProfileRead",
    "GameProfileWithPlayer",
    # Match
    "BinaryOutcome",
    "RankedOutcome",
    "Outcome",
    "MatchBase",
    "MatchCreate",
    "MatchRead",
    "MatchParticipantBase",
    "MatchParticipantCreate",
    "MatchParticipantRead",
    # Player
    "PlayerBase",
    "PlayerCreate",
    "PlayerRead",
    "PlayerUpdate",
]
