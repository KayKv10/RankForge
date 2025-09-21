# src/rankforge/schemas/match.py

"""Pydantic schemas for the Match resource."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .player import PlayerRead

# ===============================================
# == Match Participant Schemas
# ===============================================


class MatchParticipantBase(BaseModel):
    """Shared properties for a match participant."""

    player_id: int
    team_id: int

    # The `outcome` is a flexible JSON field to store results
    outcome: dict


class MatchParticipantCreate(MatchParticipantBase):
    """Properties to receive when creating a participant within a match."""

    pass


class MatchParticipantRead(MatchParticipantBase):
    """Properties to return to the client for a match participant."""

    id: int

    # Instead of just a player_id, return the full Player object.
    player: PlayerRead

    model_config = ConfigDict(from_attributes=True)


# ===============================================
# == Match Schemas
# ===============================================


class MatchBase(BaseModel):
    """Shared properties for a match."""

    game_id: int

    # The `match_metadata` is a flexible JSON field
    match_metadata: dict = Field(default_factory=dict)


class MatchCreate(MatchBase):
    """
    Properties to receive via API on create.
    This is the main payload for submitting a new match.
    """

    participants: list[MatchParticipantCreate]


class MatchRead(MatchBase):
    """Properties to return to the client for a match."""

    id: int
    played_at: datetime

    # The list of participants will use the "Read" schema to show full details.
    participants: list[MatchParticipantRead]

    model_config = ConfigDict(from_attributes=True)
