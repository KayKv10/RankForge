# src/rankforge/schemas/common.py

"""Common Pydantic schemas used across multiple resources."""

from pydantic import BaseModel, Field


class RatingInfo(BaseModel):
    """Pydantic model for Glicko-2 rating data with validation.

    This complements the RatingInfo TypedDict in models.py with actual
    runtime validation for API inputs/outputs.

    Attributes:
        rating: The player's skill rating (default: 1500.0)
        rd: Rating deviation / uncertainty (default: 350.0)
        vol: Volatility / consistency (default: 0.06)
    """

    rating: float = Field(..., ge=0, le=4000, description="Skill rating")
    rd: float = Field(..., gt=0, le=500, description="Rating deviation (uncertainty)")
    vol: float = Field(..., gt=0, le=1.0, description="Volatility (consistency)")
