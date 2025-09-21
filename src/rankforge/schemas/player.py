# src/rankforge/schemas/player.py

"""Pydantic schemas for the Player resource."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ===============================================
# Base Schema: Defines shared attributes for creation
# ===============================================
class PlayerBase(BaseModel):
    """Shared properties for a player."""

    name: str


# ===============================================
# Create Schema: Inherits the base properties
# ===============================================
class PlayerCreate(PlayerBase):
    """Properties to receive via API on create."""

    pass


# ===============================================
# Update Schema: Defines all fields as optional
# ===============================================
class PlayerUpdate(BaseModel):
    """Properties to receive via API on update, all optional."""

    name: str | None = None


# ===============================================
# Read Schema: Defines attributes for returning data
# ===============================================
class PlayerRead(PlayerBase):
    """Properties to return to the client."""

    id: int
    created_at: datetime

    # Enable ORM mode for this schema
    model_config = ConfigDict(from_attributes=True)
