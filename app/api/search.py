"""
API endpoints for search functionality.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from typing import List, Optional

from app.database import get_db
from app.models import Poem, Poet, Meter
from app.schemas.poem import PoemResponse

router = APIRouter()


@router.get("/", response_model=List[PoemResponse])
async def search_poems(
    q: Optional[str] = Query(None, description="Search query"),
    poet_id: Optional[int] = Query(None, description="Filter by poet ID"),
    meter_id: Optional[int] = Query(None, description="Filter by meter ID"),
    era: Optional[str] = Query(None, description="Filter by era"),
    literary_form: Optional[str] = Query(None, description="Filter by literary form"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Search poems with various filters.
    Supports text search and multiple filter combinations.
    """
    query = select(Poem)

    # Build filter conditions
    conditions = []

    # Text search in title and text
    if q:
        search_term = f"%{q}%"
        conditions.append(
            or_(
                Poem.title.ilike(search_term),
                Poem.text.ilike(search_term)
            )
        )

    # Filter by poet
    if poet_id:
        conditions.append(Poem.poet_id == poet_id)

    # Filter by meter
    if meter_id:
        conditions.append(Poem.meter_id == meter_id)

    # Filter by literary form
    if literary_form:
        conditions.append(Poem.literary_form.ilike(f"%{literary_form}%"))

    # Filter by era (through poet relationship)
    if era:
        query = query.join(Poet)
        conditions.append(Poet.era.ilike(f"%{era}%"))

    # Apply all conditions
    if conditions:
        query = query.where(and_(*conditions))

    # Apply pagination
    query = query.offset(skip).limit(limit)

    # Execute query
    result = await db.execute(query)
    poems = result.scalars().all()

    return poems


@router.get("/autocomplete")
async def autocomplete(
    q: str = Query(..., min_length=1, description="Search query for autocomplete"),
    db: AsyncSession = Depends(get_db),
):
    """
    Autocomplete suggestions for search.
    Returns suggestions for poems, poets, and meters.
    """
    search_term = f"%{q}%"

    # Search poems
    poem_query = select(Poem.title).where(Poem.title.ilike(search_term)).limit(5)
    poem_result = await db.execute(poem_query)
    poems = [title for (title,) in poem_result.all()]

    # Search poets
    poet_query = select(Poet.name).where(Poet.name.ilike(search_term)).limit(3)
    poet_result = await db.execute(poet_query)
    poets = [name for (name,) in poet_result.all()]

    # Search meters
    meter_query = select(Meter.name).where(Meter.name.ilike(search_term)).limit(3)
    meter_result = await db.execute(meter_query)
    meters = [name for (name,) in meter_result.all()]

    return {
        "poems": poems,
        "poets": poets,
        "meters": meters
    }
