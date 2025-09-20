# src/rankforge/api/game.py

"""API endpoints for managing games."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rankforge.db.models import Game
from rankforge.db.session import get_db
from rankforge.schemas import game as game_schema

# Creates an APIRouter instance
# - prefix="/games": All routes defined here will be prefixed with /games
# - tags=["Games"]: Groups these endpoints under "Games" in the API docs
router = APIRouter(prefix="/games", tags=["Games"])


@router.post(
    "/",
    response_model=game_schema.GameRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_game(
    game_in: game_schema.GameCreate,
    db: AsyncSession = Depends(get_db),
) -> Game:
    """
    Create a new game.

    - **name**: The unique name of the game.
    - **rating_strategy**: The identifier for the rating calculation engine.
    - **description**: An optional description of the game.
    """

    # 1. Create a new SQLAlchemy Game model instance from the Pydantic schema data
    new_game = Game(**game_in.model_dump())

    # 2. Add the new instance to the database session, commit the transaction and
    #    refresh the instance to get database-generated value (like ID)
    db.add(new_game)
    await db.commit()
    await db.refresh(new_game)

    # 3. Return the newly created game object
    #    FastAPI will automatically convert this SQLAlchemy model
    #    to the JSON response defined by `response_model=game_schema.GameRead`.
    return new_game


@router.get("/", response_model=list[game_schema.GameRead])
async def read_games(db: AsyncSession = Depends(get_db)) -> list[Game]:
    """
    Retrieve a list of all games.
    """
    # 1. Create a query via a select statement for the Game model.
    query = select(Game).order_by(Game.id)

    # 2. Execute the query.
    result = await db.execute(query)

    # 3. Get all scalar results (the Game objects themselves) from the result.
    games = result.scalars().all()

    # 4. Return the list of games.
    return list(games)


@router.get("/{game_id}", response_model=game_schema.GameRead)
async def read_game(game_id: int, db: AsyncSession = Depends(get_db)) -> Game:
    """
    Retrieve a single game by its ID.
    """
    # 1. Execute a query to find the game by its primary key.
    game = await db.get(Game, game_id)

    # 2. If the game is not found, `game` will be `None`, and will raise 404 Error.
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game with id {game_id} not found",
        )

    # 3. If the game is found, return it.
    return game


@router.put("/{game_id}", response_model=game_schema.GameRead)
async def update_game(
    game_id: int,
    game_in: game_schema.GameUpdate,
    db: AsyncSession = Depends(get_db),
) -> Game:
    """
    Update a game by its ID.
    """
    # 1. Fetch the desired game to update.
    game_to_update = await db.get(Game, game_id)
    if not game_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game with id {game_id} not found",
        )

    # 2. Get the update data from the Pydantic schema.
    #    `exclude_unset=True` creates a dict with only the fields that the client
    #    sent in the request.
    update_data = game_in.model_dump(exclude_unset=True)

    # 3. Iterate through the provided update data and set the new values
    #    on the SQLAlchemy model instance.
    for key, value in update_data.items():
        setattr(game_to_update, key, value)

    # 4. Add the instance to the session and commit.
    db.add(game_to_update)
    await db.commit()
    await db.refresh(game_to_update)

    # 5. Return the updated game object.
    return game_to_update


@router.delete("/{game_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_game(game_id: int, db: AsyncSession = Depends(get_db)) -> None:
    """
    Delete a game by its ID.
    """
    # 1. Fetch the desired game to delete.
    game_to_delete = await db.get(Game, game_id)
    if not game_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game with id {game_id} not found",
        )

    # 2. Delete the object from the database, and commit.
    await db.delete(game_to_delete)
    await db.commit()

    # 4. A 204 response has no body, sso return None.
    return None
