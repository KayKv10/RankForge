# src/rankforge/schemas/pagination.py

"""Pagination schemas and utilities for API responses."""

from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class SortOrder(str, Enum):
    """Sort order for list endpoints."""

    ASC = "asc"
    DESC = "desc"


class GameSortField(str, Enum):
    """Sortable fields for games."""

    ID = "id"
    NAME = "name"
    CREATED_AT = "created_at"


class PlayerSortField(str, Enum):
    """Sortable fields for players."""

    ID = "id"
    NAME = "name"
    CREATED_AT = "created_at"


class MatchSortField(str, Enum):
    """Sortable fields for matches."""

    ID = "id"
    PLAYED_AT = "played_at"
    CREATED_AT = "created_at"


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response wrapper.

    Attributes:
        items: List of items for the current page
        total: Total number of records matching the filters
        skip: Number of records skipped
        limit: Maximum number of records returned
        has_more: Whether more records exist beyond this page
    """

    items: list[T]
    total: int = Field(..., description="Total records matching filters")
    skip: int = Field(..., description="Records skipped")
    limit: int = Field(..., description="Max records returned")
    has_more: bool = Field(..., description="More records exist beyond this page")
