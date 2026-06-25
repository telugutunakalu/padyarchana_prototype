"""
API endpoints for poets.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from typing import List, Optional

from app.auth import require_admin
from app.database import get_db
from app.models import Poet, Poem
from app.schemas.poet import PoetCreate, PoetUpdate, PoetResponse
from app.utils.visibility import is_admin_dep, poet_visible_clause

router = APIRouter()


@router.get("/")
async def get_poets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    is_admin: bool = Depends(is_admin_dep),
):
    """Get poets with pagination, search, and poem counts. Guests only
    see public-domain poets."""
    query = select(Poet)

    if search:
        query = query.where(
            or_(
                Poet.name.ilike(f"%{search}%"),
                Poet.name_english.ilike(f"%{search}%")
            )
        )

    if not is_admin:
        query = query.where(poet_visible_clause(is_admin))

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    poets = result.scalars().all()

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
            "copyright_protected": poet.copyright_protected,
            "poem_count": poem_count or 0,
        })

    return poet_list


@router.get("/{poet_id}", response_model=PoetResponse)
async def get_poet(
    poet_id: int,
    db: AsyncSession = Depends(get_db),
    is_admin: bool = Depends(is_admin_dep),
):
    """Get a specific poet by ID. Returns 404 to guests for protected poets."""
    query = select(Poet).where(Poet.id == poet_id)
    if not is_admin:
        query = query.where(poet_visible_clause(is_admin))
    poet = (await db.execute(query)).scalar_one_or_none()

    if not poet:
        raise HTTPException(status_code=404, detail="Poet not found")

    return poet


@router.post("/", response_model=PoetResponse, status_code=201)
async def create_poet(
    poet: PoetCreate,
    db: AsyncSession = Depends(get_db),
    _admin = Depends(require_admin),
):
    """Create a new poet."""
    db_poet = Poet(**poet.model_dump())
    db.add(db_poet)
    await db.commit()
    await db.refresh(db_poet)
    return db_poet


@router.put("/{poet_id}", response_model=PoetResponse)
async def update_poet(
    poet_id: int,
    poet: PoetUpdate,
    db: AsyncSession = Depends(get_db),
    _admin = Depends(require_admin),
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
async def delete_poet(
    poet_id: int,
    db: AsyncSession = Depends(get_db),
    _admin = Depends(require_admin),
):
    """Delete a poet."""
    result = await db.execute(select(Poet).where(Poet.id == poet_id))
    db_poet = result.scalar_one_or_none()

    if not db_poet:
        raise HTTPException(status_code=404, detail="Poet not found")

    await db.delete(db_poet)
    await db.commit()
    return None
