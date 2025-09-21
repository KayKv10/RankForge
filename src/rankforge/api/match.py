# src/rankforge/api/match.py

"""API endpoints for managing matches."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from rankforge.db.models import Match, MatchParticipant
from rankforge.db.session import get_db
from rankforge.schemas import match as match_schema
from rankforge.services import match_service

# Create an APIRouter instance for matches
router = APIRouter(prefix="/matches", tags=["Matches"])


@router.get("/", response_model=list[match_schema.MatchRead])
async def read_matches(db: AsyncSession = Depends(get_db)) -> list[Match]:
    """
    Retrieve a list of all matches, including participants and players.
    """
    # Create a query via a select statement
    query = (
        select(Match)
        .order_by(Match.id)
        .options(selectinload(Match.participants).selectinload(MatchParticipant.player))
    )

    # Execute the query.
    result = await db.execute(query)

    # Get all scalar results (the Match objects themselves) from the result.
    matches = result.scalars().all()
    return list(matches)


@router.post(
    "/", response_model=match_schema.MatchRead, status_code=status.HTTP_201_CREATED
)
async def create_match(
    match_in: match_schema.MatchCreate, db: AsyncSession = Depends(get_db)
) -> Match:
    """
    Create a new match, process ratings, and return the created match.
    """
    created_match = await match_service.process_new_match(db, match_in)
    return created_match


@router.get("/{match_id}", response_model=match_schema.MatchRead)
async def read_match(match_id: int, db: AsyncSession = Depends(get_db)) -> Match:
    """
    Retrieve a single match by its ID, including its participants and their players.
    """
    # 1. Build a query to select the Match.
    # 2. Use `options` and `selectinload` to create an efficient query that
    #    "eager loads" the related participants and their nested player objects.
    #    This prevents the "N+1 problem" by issuing just two extra queries
    #    (one for all participants, one for all players) instead of one per participant.
    query = (
        select(Match)
        .where(Match.id == match_id)
        .options(selectinload(Match.participants).selectinload(MatchParticipant.player))
    )

    result = await db.execute(query)
    match = result.scalar_one_or_none()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match with id {match_id} not found",
        )

    return match


@router.delete("/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_match(match_id: int, db: AsyncSession = Depends(get_db)) -> None:
    """
    Delete a match by its ID.
    """
    # Fetch the match to delete
    match_to_delete = await db.get(Match, match_id)
    if not match_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match with id {match_id} not found",
        )

    # Delete from the database. Thanks to `cascade="all, delete-orphan"` in our
    # `models.py` relationship, SQLAlchemy will automatically delete all
    # associated MatchParticipant records as well.
    await db.delete(match_to_delete)
    await db.commit()

    return None
