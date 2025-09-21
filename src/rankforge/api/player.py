# src/rankforge/api/player.py

"""API endpoints for managing players."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rankforge.db.models import Player
from rankforge.db.session import get_db
from rankforge.schemas import player as player_schema

# Create an APIRouter instance for players
# - prefix="/players": All routes here will be prefixed with /players
# - tags=["Players"]: Groups these endpoints under "Players" in the API docs
router = APIRouter(prefix="/players", tags=["Players"])


@router.post(
    "/",
    response_model=player_schema.PlayerRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_player(
    player_in: player_schema.PlayerCreate, db: AsyncSession = Depends(get_db)
) -> Player:
    """
    Create a new player.

    - **name**: The unique name for the player.
    """
    # Create a new SQLAlchemy Player model instance
    new_player = Player(**player_in.model_dump())

    # Add, commit, and refresh to save to the database and get the new ID
    db.add(new_player)
    await db.commit()
    await db.refresh(new_player)

    # Return the newly created player object
    return new_player


@router.get("/", response_model=list[player_schema.PlayerRead])
async def read_players(db: AsyncSession = Depends(get_db)) -> list[Player]:
    """
    Retrieve a list of all players.
    """
    # Create a query via a select statement
    query = select(Player).order_by(Player.id)

    # Execute the query.
    result = await db.execute(query)

    # Get all scalar results (the Player objects themselves) from the result.
    players = result.scalars().all()

    # Return list of players.
    return list(players)


@router.get("/{player_id}", response_model=player_schema.PlayerRead)
async def read_player(player_id: int, db: AsyncSession = Depends(get_db)) -> Player:
    """
    Retrieve a single player by their ID.
    """
    # Fetch player by Primary Key
    player = await db.get(Player, player_id)

    # If not found, raise a standard 404 error
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with id {player_id} not found",
        )

    # Return the found player object
    return player


@router.put("/{player_id}", response_model=player_schema.PlayerRead)
async def update_player(
    player_id: int,
    player_in: player_schema.PlayerUpdate,
    db: AsyncSession = Depends(get_db),
) -> Player:
    """
    Update a player's name.
    """
    # Fetch the existing player
    player_to_update = await db.get(Player, player_id)
    if not player_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with id {player_id} not found",
        )

    # Get the update data, excluding fields that were not sent
    update_data = player_in.model_dump(exclude_unset=True)

    # Update the model instance with the new data
    for key, value in update_data.items():
        setattr(player_to_update, key, value)

    # Add, commit, and refresh
    db.add(player_to_update)
    await db.commit()
    await db.refresh(player_to_update)

    return player_to_update


@router.delete("/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_player(player_id: int, db: AsyncSession = Depends(get_db)) -> None:
    """
    Delete a player by their ID.
    """
    # Fetch the player to delete
    player_to_delete = await db.get(Player, player_id)
    if not player_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with id {player_id} not found",
        )

    # Delete from the database
    await db.delete(player_to_delete)
    await db.commit()

    # Return None for the 204 No Content response
    return None
