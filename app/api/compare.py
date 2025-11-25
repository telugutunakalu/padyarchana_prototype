"""
API endpoints for comparative analysis.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db

router = APIRouter()


@router.get("/poems")
async def compare_poems(
    poem_ids: List[int] = Query(..., description="List of poem IDs to compare"),
    db: AsyncSession = Depends(get_db),
):
    """
    Compare multiple poems based on structure, vocabulary, and metadata.
    """
    if len(poem_ids) < 2:
        raise HTTPException(
            status_code=400, detail="At least 2 poem IDs are required for comparison"
        )

    # TODO: Implement poem comparison logic
    return {
        "poems": poem_ids,
        "comparison": {
            "vocabulary": {},
            "structure": {},
            "metadata": {},
        },
    }


@router.get("/poets")
async def compare_poets(
    poet_ids: List[int] = Query(..., description="List of poet IDs to compare"),
    db: AsyncSession = Depends(get_db),
):
    """
    Compare multiple poets based on stylistic elements.
    """
    if len(poet_ids) < 2:
        raise HTTPException(
            status_code=400, detail="At least 2 poet IDs are required for comparison"
        )

    # TODO: Implement poet comparison logic
    return {
        "poets": poet_ids,
        "comparison": {
            "vocabulary_usage": {},
            "preferred_meters": {},
            "sandhi_samasa_usage": {},
        },
    }
