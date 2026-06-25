"""
API endpoints for search functionality.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, text as sa_text
from typing import List, Optional

from app.database import get_db
from app.models import Poem, Poet, Meter
from app.schemas.poem import PoemResponse
from app.utils.visibility import is_admin_dep, poem_visible_clause, poet_visible_clause

router = APIRouter()


def _escape_fts5_query(q: str) -> str:
    """Wrap user input as a single double-quoted FTS5 phrase so trigrams,
    apostrophes, and other special chars pass through unparsed."""
    return '"' + q.replace('"', '""') + '"'


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
    is_admin: bool = Depends(is_admin_dep),
):
    """
    Search poems with various filters.

    Text matching uses an FTS5 trigram index over title + text + bhavam +
    flattened prathipadartham, so a partial word (>=3 chars) hits anywhere
    in any of those fields. Shorter queries fall back to ilike substring scan.

    Guests only get poems whose poet is public-domain; admin sees all.
    """
    use_fts = bool(q) and len(q.strip()) >= 3
    q_stripped = q.strip() if q else None

    if use_fts:
        # FTS5 prefilter: rowid ↔ poems.id. Pull a generous pool and let the
        # other filters narrow further; we still LIMIT at the end.
        fts_sql = sa_text(
            "SELECT rowid FROM poems_fts WHERE poems_fts MATCH :q"
        ).bindparams(q=_escape_fts5_query(q_stripped))
        fts_rows = await db.execute(fts_sql)
        candidate_ids = [r[0] for r in fts_rows.fetchall()]
        if not candidate_ids:
            return []
        query = select(Poem).where(Poem.id.in_(candidate_ids))
    else:
        query = select(Poem)

    conditions = []

    # Short-query fallback: substring on title/text/bhavam.
    if q_stripped and not use_fts:
        like = f"%{q_stripped}%"
        conditions.append(
            or_(
                Poem.title.ilike(like),
                Poem.text.ilike(like),
                Poem.bhavam.ilike(like),
            )
        )

    if poet_id:
        conditions.append(Poem.poet_id == poet_id)
    if meter_id:
        conditions.append(Poem.meter_id == meter_id)
    if literary_form:
        conditions.append(Poem.literary_form.ilike(f"%{literary_form}%"))
    if era:
        query = query.join(Poet)
        conditions.append(Poet.era.ilike(f"%{era}%"))

    if conditions:
        query = query.where(and_(*conditions))

    # Copyright visibility: guests only see poems from PD poets.
    if not is_admin:
        query = query.where(poem_visible_clause(is_admin))

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/autocomplete")
async def autocomplete(
    q: str = Query(..., min_length=1, description="Search query for autocomplete"),
    db: AsyncSession = Depends(get_db),
    is_admin: bool = Depends(is_admin_dep),
):
    """
    Autocomplete suggestions for search.
    Returns suggestions for poems, poets, and meters. Guest queries are
    filtered to public-domain content.
    """
    search_term = f"%{q}%"

    # Search poems — guests only see PD-author poems.
    poem_query = select(Poem.title).where(Poem.title.ilike(search_term))
    if not is_admin:
        poem_query = poem_query.where(poem_visible_clause(is_admin))
    poem_result = await db.execute(poem_query.limit(5))
    poems = [title for (title,) in poem_result.all()]

    # Search poets — guests only see PD poets.
    poet_query = select(Poet.name).where(Poet.name.ilike(search_term))
    if not is_admin:
        poet_query = poet_query.where(poet_visible_clause(is_admin))
    poet_result = await db.execute(poet_query.limit(3))
    poets = [name for (name,) in poet_result.all()]

    # Meters are not authored — show all.
    meter_query = select(Meter.name).where(Meter.name.ilike(search_term)).limit(3)
    meter_result = await db.execute(meter_query)
    meters = [name for (name,) in meter_result.all()]

    return {
        "poems": poems,
        "poets": poets,
        "meters": meters
    }
