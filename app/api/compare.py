"""
API endpoints for comparative analysis.

This module provides endpoints for comparing poems and poets based on
various linguistic and stylistic metrics. The comparison features are
planned for future implementation.
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

    Planned comparison features:
    - Vocabulary overlap analysis (shared words, unique words per poem)
    - Structural comparison (line count, word count, meter patterns)
    - Metadata comparison (poet era, literary form, source)
    - Prosodic analysis (guru-laghu distribution comparison)

    Args:
        poem_ids: List of at least 2 poem IDs to compare

    Returns:
        Comparison results with vocabulary, structure, and metadata analysis

    Note:
        This endpoint is currently a stub. Full implementation pending.
    """
    if len(poem_ids) < 2:
        raise HTTPException(
            status_code=400, detail="At least 2 poem IDs are required for comparison"
        )

    # TODO: Implement poem comparison logic
    # - Fetch poems from database
    # - Analyze vocabulary overlap using aksharanusarika
    # - Compare structural metrics
    # - Return detailed comparison results
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

    Planned comparison features:
    - Vocabulary usage patterns (common vs distinctive word choices)
    - Preferred meters analysis (which chandassu each poet favors)
    - Sandhi and samasa usage frequency
    - Era and biographical comparison

    Args:
        poet_ids: List of at least 2 poet IDs to compare

    Returns:
        Comparison results with stylistic analysis across poets

    Note:
        This endpoint is currently a stub. Full implementation pending.
    """
    if len(poet_ids) < 2:
        raise HTTPException(
            status_code=400, detail="At least 2 poet IDs are required for comparison"
        )

    # TODO: Implement poet comparison logic
    # - Fetch all poems by each poet
    # - Aggregate vocabulary and style metrics
    # - Compare meter preferences
    # - Return detailed comparison results
    return {
        "poets": poet_ids,
        "comparison": {
            "vocabulary_usage": {},
            "preferred_meters": {},
            "sandhi_samasa_usage": {},
        },
    }
