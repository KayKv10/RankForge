# src/rankforge/db/models.py

"""Database models for the RankForge application."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List

from sqlalchemy import (
    JSON,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    declarative_base,
    mapped_column,
    relationship,
)

Base = declarative_base()

# ===============================================
# Core Tables: Player and Game
# ===============================================


class Player(Base):
    """Represents a unique person across all games."""

    __tablename__ = "players"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    # Optional: could store Discord ID, etc. for future integrations

    # A player has a collection of profiles, one for each game they play
    game_profiles: Mapped[List["GameProfile"]] = relationship(
        back_populates="player", cascade="all, delete-orphan"
    )
    match_participations: Mapped[List["MatchParticipant"]] = relationship(
        back_populates="player"
    )

    def __init__(self, name: str, **kw: Any):
        super().__init__(**kw)
        self.name = name


class Game(Base):
    """Represents a game that can be played."""

    __tablename__ = "games"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    # The name of the calculation strategy,
    # e.g., 'glicko2_team_binary', 'glicko2_hybrid_ranked'
    rating_strategy: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)

    # A game has many profiles associated with it
    game_profiles: Mapped[List["GameProfile"]] = relationship(
        back_populates="game", cascade="all, delete-orphan"
    )
    matches: Mapped[List["Match"]] = relationship(back_populates="game")


class GameProfile(Base):
    """Stores a player's rating and stats for a specific game."""

    __tablename__ = "game_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False)

    # Flexible JSON blob to hold all rating info.
    # Ex: {'main': {'rating': 1500, 'rd': 350}, 'solo': {'rating': 1400, 'rd': 300}}
    # Ex: {'rating': 1500, 'rd': 350, 'volatility': 0.06}
    rating_info: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Flexible JSON blob for stats.
    # Ex: {'wins': 10, 'losses': 5, 'win_rate': 0.66, 'spymaster_wins': 4}
    stats: Mapped[dict] = mapped_column(JSON, default=lambda: {})

    player: Mapped["Player"] = relationship(back_populates="game_profiles")
    game: Mapped["Game"] = relationship(back_populates="game_profiles")

    __table_args__ = (UniqueConstraint("player_id", "game_id", name="_player_game_uc"),)


# ===============================================
# Match and Results Tables
# ===============================================


class Match(Base):
    """Represents a single instance of a game being played."""

    __tablename__ = "matches"
    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False)
    played_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    # Pillar 3: Contextual Metadata
    # Ex: {'map': 'A Diverse World', 'game_length': '3 minutes',
    #       'championship_match': true}
    match_metadata: Mapped[dict] = mapped_column(JSON, default=lambda: {})

    game: Mapped["Game"] = relationship(back_populates="matches")
    participants: Mapped[List["MatchParticipant"]] = relationship(
        back_populates="match", cascade="all, delete-orphan"
    )


class MatchParticipant(Base):
    """Links a Player to a Match, recording their specific involvement and result."""

    __tablename__ = "match_participants"
    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)

    # Pillar 1: Participation Structure
    # An integer to group players into teams for this match.
    # For free-for-all, each player can have a unique team_id.
    team_id: Mapped[int] = mapped_column(nullable=False)

    # Pillar 2: Performance Data
    # The single source of truth for the result.
    # Golf Ex: {'team_rank': 1, 'individual_rank': 3, 'score': -4}
    # Geoguessr Ex: {'result': 'win', 'score': 24150}
    outcome: Mapped[dict] = mapped_column(JSON, nullable=False)

    # For auditing and historical analysis
    rating_info_before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    rating_info_change: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    player: Mapped["Player"] = relationship(back_populates="match_participations")
    match: Mapped["Match"] = relationship(back_populates="participants")
