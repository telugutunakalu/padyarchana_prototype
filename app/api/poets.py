"""
API endpoints for poets.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from typing import List, Optional

from app.database import get_db
from app.models import Poet, Poem
from app.schemas.poet import PoetCreate, PoetUpdate, PoetResponse

router = APIRouter()


@router.get("/")
async def get_poets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get all poets with pagination, search, and poem counts."""
    query = select(Poet)

    if search:
        query = query.where(
            or_(
                Poet.name.ilike(f"%{search}%"),
                Poet.name_english.ilike(f"%{search}%")
            )
        )

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    poets = result.scalars().all()

    # Get poem counts for each poet
    poet_list = []
    for poet in poets:
        poem_count = await db.scalar(
            select(func.count(Poem.id)).where(Poem.poet_id == poet.id)
        )
        poet_list.append({
            "id": poet.id,
            "name": poet.name,
            "name_english": poet.name_english,
            "biography": poet.biography,
            "era": poet.era,
            "birth_year": poet.birth_year,
            "death_year": poet.death_year,
            "poem_count": poem_count or 0
        })

    return poet_list


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
