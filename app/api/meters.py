"""
API endpoints for meters/chandassu.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models import Meter
from app.schemas.meter import MeterCreate, MeterUpdate, MeterResponse

router = APIRouter()


@router.get("/", response_model=List[MeterResponse])
async def get_meters(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get all meters with pagination."""
    result = await db.execute(select(Meter).offset(skip).limit(limit))
    meters = result.scalars().all()
    return meters


@router.get("/{meter_id}", response_model=MeterResponse)
async def get_meter(meter_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific meter by ID."""
    result = await db.execute(select(Meter).where(Meter.id == meter_id))
    meter = result.scalar_one_or_none()

    if not meter:
        raise HTTPException(status_code=404, detail="Meter not found")

    return meter


@router.post("/", response_model=MeterResponse, status_code=201)
async def create_meter(meter: MeterCreate, db: AsyncSession = Depends(get_db)):
    """Create a new meter."""
    db_meter = Meter(**meter.model_dump())
    db.add(db_meter)
    await db.commit()
    await db.refresh(db_meter)
    return db_meter


@router.put("/{meter_id}", response_model=MeterResponse)
async def update_meter(
    meter_id: int, meter: MeterUpdate, db: AsyncSession = Depends(get_db)
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
async def delete_meter(meter_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a meter."""
    result = await db.execute(select(Meter).where(Meter.id == meter_id))
    db_meter = result.scalar_one_or_none()

    if not db_meter:
        raise HTTPException(status_code=404, detail="Meter not found")

    await db.delete(db_meter)
    await db.commit()
    return None
