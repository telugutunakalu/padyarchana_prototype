"""
API endpoints for poems.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models import Poem
from app.schemas.poem import PoemCreate, PoemUpdate, PoemResponse, PoemDetail

router = APIRouter()


@router.get("/", response_model=List[PoemResponse])
async def get_poems(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get all poems with pagination."""
    result = await db.execute(select(Poem).offset(skip).limit(limit))
    poems = result.scalars().all()
    return poems


@router.get("/{poem_id}", response_model=PoemDetail)
async def get_poem(poem_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific poem by ID."""
    result = await db.execute(select(Poem).where(Poem.id == poem_id))
    poem = result.scalar_one_or_none()

    if not poem:
        raise HTTPException(status_code=404, detail="Poem not found")

    return poem


@router.post("/", response_model=PoemResponse, status_code=201)
async def create_poem(poem: PoemCreate, db: AsyncSession = Depends(get_db)):
    """Create a new poem."""
    db_poem = Poem(**poem.model_dump())
    db.add(db_poem)
    await db.commit()
    await db.refresh(db_poem)
    return db_poem


@router.put("/{poem_id}", response_model=PoemResponse)
async def update_poem(
    poem_id: int, poem: PoemUpdate, db: AsyncSession = Depends(get_db)
):
    """Update a poem."""
    result = await db.execute(select(Poem).where(Poem.id == poem_id))
    db_poem = result.scalar_one_or_none()

    if not db_poem:
        raise HTTPException(status_code=404, detail="Poem not found")

    update_data = poem.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_poem, key, value)

    await db.commit()
    await db.refresh(db_poem)
    return db_poem


@router.delete("/{poem_id}", status_code=204)
async def delete_poem(poem_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a poem."""
    result = await db.execute(select(Poem).where(Poem.id == poem_id))
    db_poem = result.scalar_one_or_none()

    if not db_poem:
        raise HTTPException(status_code=404, detail="Poem not found")

    await db.delete(db_poem)
    await db.commit()
    return None
