"""
API endpoints for meters/chandassu.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from typing import List, Optional

from app.auth import require_admin
from app.database import get_db
from app.models import Meter, Poem
from app.schemas.meter import MeterCreate, MeterUpdate, MeterResponse
from app.utils.visibility import is_admin_dep, poem_visible_clause

router = APIRouter()


@router.get("/")
async def get_meters(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    is_admin: bool = Depends(is_admin_dep),
):
    """Get all meters with pagination, search, and poem counts.

    Poem counts are filtered to public-domain poems for guests, so a
    meter whose only poems are by protected authors will show 0 for
    guests."""
    query = select(Meter)

    if search:
        query = query.where(
            or_(
                Meter.name.ilike(f"%{search}%"),
                Meter.name_english.ilike(f"%{search}%")
            )
        )

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    meters = result.scalars().all()

    meter_list = []
    for meter in meters:
        count_q = select(func.count(Poem.id)).where(Poem.meter_id == meter.id)
        if not is_admin:
            count_q = count_q.where(poem_visible_clause(is_admin))
        poem_count = await db.scalar(count_q)
        meter_list.append({
            "id": meter.id,
            "name": meter.name,
            "name_english": meter.name_english,
            "description": meter.description,
            "gana_structure": meter.gana_structure,
            "example_pattern": meter.example_pattern,
            "poem_count": poem_count or 0
        })

    return meter_list


@router.get("/{meter_id}", response_model=MeterResponse)
async def get_meter(meter_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific meter by ID."""
    result = await db.execute(select(Meter).where(Meter.id == meter_id))
    meter = result.scalar_one_or_none()

    if not meter:
        raise HTTPException(status_code=404, detail="Meter not found")

    return meter


@router.post("/", response_model=MeterResponse, status_code=201)
async def create_meter(
    meter: MeterCreate,
    db: AsyncSession = Depends(get_db),
    _admin = Depends(require_admin),
):
    """Create a new meter."""
    db_meter = Meter(**meter.model_dump())
    db.add(db_meter)
    await db.commit()
    await db.refresh(db_meter)
    return db_meter


@router.put("/{meter_id}", response_model=MeterResponse)
async def update_meter(
    meter_id: int,
    meter: MeterUpdate,
    db: AsyncSession = Depends(get_db),
    _admin = Depends(require_admin),
):
    """Update a meter."""
    result = await db.execute(select(Meter).where(Meter.id == meter_id))
    db_meter = result.scalar_one_or_none()

    if not db_meter:
        raise HTTPException(status_code=404, detail="Meter not found")

    update_data = meter.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_meter, key, value)

    await db.commit()
    await db.refresh(db_meter)
    return db_meter


@router.delete("/{meter_id}", status_code=204)
async def delete_meter(
    meter_id: int,
    db: AsyncSession = Depends(get_db),
    _admin = Depends(require_admin),
):
    """Delete a meter."""
    result = await db.execute(select(Meter).where(Meter.id == meter_id))
    db_meter = result.scalar_one_or_none()

    if not db_meter:
        raise HTTPException(status_code=404, detail="Meter not found")

    await db.delete(db_meter)
    await db.commit()
    return None
