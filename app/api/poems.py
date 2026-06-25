"""
API endpoints for poems.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from app.auth import require_admin
from app.database import get_db
from app.models import Poem, Poet
from app.schemas.poem import PoemCreate, PoemUpdate, PoemResponse, PoemDetail
from app.utils.search_text import build_search_text
from app.utils.visibility import is_admin_dep, poem_visible_clause

router = APIRouter()

# Fields whose change should refresh the FTS5-indexed search_text blob.
_SEARCH_RELEVANT_FIELDS = {"title", "text", "bhavam", "prathipadartham"}


@router.get("/", response_model=List[PoemResponse])
async def get_poems(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    poet_id: int = Query(None, description="Filter by poet ID"),
    db: AsyncSession = Depends(get_db),
    is_admin: bool = Depends(is_admin_dep),
):
    """Get poems with pagination. Guests only see PD-author poems."""
    query = select(Poem)
    if poet_id:
        query = query.where(Poem.poet_id == poet_id)
    if not is_admin:
        query = query.where(poem_visible_clause(is_admin))
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{poem_id}", response_model=PoemDetail)
async def get_poem(
    poem_id: int,
    db: AsyncSession = Depends(get_db),
    is_admin: bool = Depends(is_admin_dep),
):
    """Get a specific poem by ID. Returns 404 to guests if the poem's
    poet is copyright-protected."""
    query = select(Poem).where(Poem.id == poem_id).options(
        selectinload(Poem.poet), selectinload(Poem.meter)
    )
    if not is_admin:
        query = query.where(poem_visible_clause(is_admin))
    poem = (await db.execute(query)).scalar_one_or_none()

    if not poem:
        raise HTTPException(status_code=404, detail="Poem not found")

    return poem


@router.post("/", response_model=PoemResponse, status_code=201)
async def create_poem(
    poem: PoemCreate,
    db: AsyncSession = Depends(get_db),
    _admin = Depends(require_admin),
):
    """Create a new poem."""
    data = poem.model_dump()
    # Populate search_text so the FTS5 trigger indexes the new row correctly.
    data["search_text"] = build_search_text(
        data.get("title"), data.get("text"), data.get("bhavam"), data.get("prathipadartham")
    )
    db_poem = Poem(**data)
    db.add(db_poem)
    await db.commit()
    await db.refresh(db_poem)
    return db_poem


@router.put("/{poem_id}", response_model=PoemResponse)
async def update_poem(
    poem_id: int,
    poem: PoemUpdate,
    db: AsyncSession = Depends(get_db),
    _admin = Depends(require_admin),
):
    """Update a poem."""
    result = await db.execute(select(Poem).where(Poem.id == poem_id))
    db_poem = result.scalar_one_or_none()

    if not db_poem:
        raise HTTPException(status_code=404, detail="Poem not found")

    update_data = poem.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_poem, key, value)

    # If any searchable field changed, recompute search_text so FTS5 stays
    # in sync. The poems_fts AFTER UPDATE trigger fires on this change.
    if update_data.keys() & _SEARCH_RELEVANT_FIELDS:
        db_poem.search_text = build_search_text(
            db_poem.title, db_poem.text, db_poem.bhavam, db_poem.prathipadartham
        )

    await db.commit()
    await db.refresh(db_poem)
    return db_poem


@router.delete("/{poem_id}", status_code=204)
async def delete_poem(
    poem_id: int,
    db: AsyncSession = Depends(get_db),
    _admin = Depends(require_admin),
):
    """Delete a poem."""
    result = await db.execute(select(Poem).where(Poem.id == poem_id))
    db_poem = result.scalar_one_or_none()

    if not db_poem:
        raise HTTPException(status_code=404, detail="Poem not found")

    await db.delete(db_poem)
    await db.commit()
    return None
