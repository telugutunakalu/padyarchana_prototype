"""
API endpoints for poems.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List

from app.auth import require_admin
from app.database import get_db
from app.models import Poem, Poet, PoemVersion
from app.schemas.poem import (
    PoemCreate, PoemUpdate, PoemResponse, PoemDetail,
    PoemVersionSummary, PoemVersionDetail,
)
from app.utils.search_text import build_search_text
from app.utils.visibility import is_admin_dep, poem_visible_clause

router = APIRouter()

# Fields whose change should refresh the FTS5-indexed search_text blob.
_SEARCH_RELEVANT_FIELDS = {"title", "text", "bhavam", "prathipadartham"}

# Content fields whose change is worth tracking as a new version. Curatorial
# metadata like `rating` (the gold/silver/bronze grade) and `meter_id` are
# deliberately NOT here — grading/classifying a poem is not editing its content,
# so it must not spawn a version.
_VERSION_TRIGGER_FIELDS = ("title", "text", "bhavam", "prathipadartham")

# What a version row stores. We snapshot the full editable set (so a version is
# a complete picture), even though only the trigger fields above start one.
_VERSION_SNAPSHOT_FIELDS = (
    "title", "text", "bhavam", "prathipadartham", "meter_id", "rating", "literary_form",
)


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


@router.get("/{poem_id}/neighbors")
async def get_poem_neighbors(
    poem_id: int,
    db: AsyncSession = Depends(get_db),
    is_admin: bool = Depends(is_admin_dep),
):
    """Previous/next poem ids in ascending id order, respecting visibility.
    Either may be null at the ends of the (visible) sequence. IDs are gappy,
    so this returns the nearest existing neighbour, not poem_id ± 1."""
    prev_q = select(Poem.id).where(Poem.id < poem_id).order_by(Poem.id.desc()).limit(1)
    next_q = select(Poem.id).where(Poem.id > poem_id).order_by(Poem.id.asc()).limit(1)
    if not is_admin:
        vis = poem_visible_clause(is_admin)
        prev_q = prev_q.where(vis)
        next_q = next_q.where(vis)

    prev_id = (await db.execute(prev_q)).scalar_one_or_none()
    next_id = (await db.execute(next_q)).scalar_one_or_none()
    return {"prev_id": prev_id, "next_id": next_id}


@router.get("/{poem_id}/versions", response_model=List[PoemVersionSummary])
async def list_poem_versions(
    poem_id: int,
    db: AsyncSession = Depends(get_db),
    _admin = Depends(require_admin),
):
    """List archived versions (v1, v2, …) of a poem, oldest first. Admin-only."""
    result = await db.execute(
        select(PoemVersion)
        .where(PoemVersion.poem_id == poem_id)
        .order_by(PoemVersion.version_no.asc())
    )
    return result.scalars().all()


@router.get("/{poem_id}/versions/{version_no}", response_model=PoemVersionDetail)
async def get_poem_version(
    poem_id: int,
    version_no: int,
    db: AsyncSession = Depends(get_db),
    _admin = Depends(require_admin),
):
    """Return a single archived version's full content. Admin-only."""
    result = await db.execute(
        select(PoemVersion).where(
            PoemVersion.poem_id == poem_id,
            PoemVersion.version_no == version_no,
        )
    )
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return version


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
    admin = Depends(require_admin),
):
    """Update a poem. Before applying changes, archive the current content as
    the next version (v1, v2, …) so the edit history is preserved."""
    result = await db.execute(select(Poem).where(Poem.id == poem_id))
    db_poem = result.scalar_one_or_none()

    if not db_poem:
        raise HTTPException(status_code=404, detail="Poem not found")

    update_data = poem.model_dump(exclude_unset=True)

    # Archive the pre-edit state only when actual content (text / title /
    # prathipadartham / bhavam) changes — not for rating or meter tweaks — so we
    # keep a clean v1/v2/v3 trail toward the gold standard.
    content_changed = any(
        f in update_data and getattr(db_poem, f) != update_data[f]
        for f in _VERSION_TRIGGER_FIELDS
    )
    if content_changed:
        next_no = (
            await db.execute(
                select(func.coalesce(func.max(PoemVersion.version_no), 0))
                .where(PoemVersion.poem_id == poem_id)
            )
        ).scalar() + 1
        db.add(PoemVersion(
            poem_id=poem_id,
            version_no=next_no,
            created_by=getattr(admin, "username", None),
            **{f: getattr(db_poem, f) for f in _VERSION_SNAPSHOT_FIELDS},
        ))

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
