"""
API endpoints for poets.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models import Poet
from app.schemas.poet import PoetCreate, PoetUpdate, PoetResponse

router = APIRouter()


@router.get("/", response_model=List[PoetResponse])
async def get_poets(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get all poets with pagination."""
    result = await db.execute(select(Poet).offset(skip).limit(limit))
    poets = result.scalars().all()
    return poets


@router.get("/{poet_id}", response_model=PoetResponse)
async def get_poet(poet_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific poet by ID."""
    result = await db.execute(select(Poet).where(Poet.id == poet_id))
    poet = result.scalar_one_or_none()

    if not poet:
        raise HTTPException(status_code=404, detail="Poet not found")

    return poet


@router.post("/", response_model=PoetResponse, status_code=201)
async def create_poet(poet: PoetCreate, db: AsyncSession = Depends(get_db)):
    """Create a new poet."""
    db_poet = Poet(**poet.model_dump())
    db.add(db_poet)
    await db.commit()
    await db.refresh(db_poet)
    return db_poet


@router.put("/{poet_id}", response_model=PoetResponse)
async def update_poet(
    poet_id: int, poet: PoetUpdate, db: AsyncSession = Depends(get_db)
):
    """Update a poet."""
    result = await db.execute(select(Poet).where(Poet.id == poet_id))
    db_poet = result.scalar_one_or_none()

    if not db_poet:
        raise HTTPException(status_code=404, detail="Poet not found")

    update_data = poet.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_poet, key, value)

    await db.commit()
    await db.refresh(db_poet)
    return db_poet


@router.delete("/{poet_id}", status_code=204)
async def delete_poet(poet_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a poet."""
    result = await db.execute(select(Poet).where(Poet.id == poet_id))
    db_poet = result.scalar_one_or_none()

    if not db_poet:
        raise HTTPException(status_code=404, detail="Poet not found")

    await db.delete(db_poet)
    await db.commit()
    return None
