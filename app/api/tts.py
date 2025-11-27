"""
API endpoints for TTS audio generation, retrieval, and batch management.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import Poem, PoemTTSAudio, TTSBatchJob, JobStatus
from app.services.tts_service import get_or_generate_tts, get_tts_status, run_batch_tts_job

router = APIRouter()


# =============================================================================
# Single Poem TTS Endpoints
# =============================================================================

@router.get("/poems/{poem_id}/tts")
async def get_poem_tts(
    poem_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get TTS audio status for a poem.
    Returns exists=false if TTS hasn't been generated yet.
    """
    tts = await get_tts_status(db, poem_id)

    if not tts:
        return {"exists": False, "poem_id": poem_id, "message": "TTS not generated yet"}

    return {
        "exists": True,
        "poem_id": poem_id,
        "audio_url": f"/static/tts_audio/{tts.filename}",
        "duration_seconds": tts.duration_seconds,
        "file_size_bytes": tts.file_size_bytes,
        "voice_description": tts.voice_description,
        "generated_at": tts.generated_at.isoformat() if tts.generated_at else None
    }


@router.post("/poems/{poem_id}/tts/generate")
async def generate_poem_tts(
    poem_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger TTS generation for a specific poem.
    This is a blocking operation that may take 1-5 minutes.
    """
    # Verify poem exists
    result = await db.execute(select(Poem).where(Poem.id == poem_id))
    poem = result.scalar_one_or_none()
    if not poem:
        raise HTTPException(404, "Poem not found")

    # Generate TTS (blocking)
    tts = await get_or_generate_tts(db, poem_id)
    if not tts:
        raise HTTPException(500, "Failed to generate TTS")

    return {
        "status": "generated",
        "poem_id": poem_id,
        "audio_url": f"/static/tts_audio/{tts.filename}",
        "duration_seconds": tts.duration_seconds,
        "file_size_bytes": tts.file_size_bytes
    }


# =============================================================================
# TTS Statistics Endpoint
# =============================================================================

@router.get("/tts/stats")
async def get_tts_stats(db: AsyncSession = Depends(get_db)):
    """Get TTS generation statistics."""
    total_poems = await db.scalar(select(func.count(Poem.id)))
    poems_with_tts = await db.scalar(select(func.count(PoemTTSAudio.id)))

    poems_without_tts = total_poems - poems_with_tts
    coverage_percent = round((poems_with_tts / total_poems) * 100, 1) if total_poems > 0 else 0

    return {
        "total_poems": total_poems,
        "poems_with_tts": poems_with_tts,
        "poems_without_tts": poems_without_tts,
        "coverage_percent": coverage_percent
    }


# =============================================================================
# Batch Job Management Endpoints
# =============================================================================

@router.get("/tts/jobs")
async def get_batch_jobs(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get recent batch jobs."""
    result = await db.execute(
        select(TTSBatchJob)
        .order_by(TTSBatchJob.created_at.desc())
        .limit(limit)
    )
    jobs = result.scalars().all()

    return [
        {
            "id": job.id,
            "status": job.status,
            "total_poems": job.total_poems,
            "completed_poems": job.completed_poems,
            "failed_poems": job.failed_poems,
            "progress_percent": job.progress_percent,
            "current_poem_id": job.current_poem_id,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "created_at": job.created_at.isoformat() if job.created_at else None,
        }
        for job in jobs
    ]


@router.post("/tts/batch/start")
async def start_batch_job(
    limit: int = 20,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Start a new batch TTS generation job.
    Options:
    - limit=20: Generate next 20 poems without TTS
    - limit=50: Generate next 50 poems
    - limit=100: Generate next 100 poems
    - limit=0: Generate ALL remaining poems
    """
    # Count poems without TTS
    poems_without_tts = await db.scalar(
        select(func.count(Poem.id))
        .outerjoin(PoemTTSAudio)
        .where(PoemTTSAudio.id == None)
    )

    if poems_without_tts == 0:
        return {"status": "complete", "message": "All poems already have TTS audio"}

    # Calculate actual limit
    actual_limit = min(limit, poems_without_tts) if limit > 0 else poems_without_tts

    # Create job record
    job = TTSBatchJob(
        status=JobStatus.PENDING.value,
        total_poems=actual_limit,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Start background task
    if background_tasks:
        background_tasks.add_task(run_batch_tts_job, job.id, actual_limit)

    return {
        "status": "started",
        "job_id": job.id,
        "poems_to_process": actual_limit
    }


@router.post("/tts/batch/{job_id}/cancel")
async def cancel_batch_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Cancel a running batch job."""
    result = await db.execute(
        select(TTSBatchJob).where(TTSBatchJob.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(404, "Job not found")

    if job.status == JobStatus.RUNNING.value:
        job.status = JobStatus.CANCELLED.value
        await db.commit()
        return {"status": "cancelled", "job_id": job_id}

    return {"status": job.status, "message": "Job is not running"}


# =============================================================================
# Poems TTS Status List (for Admin)
# =============================================================================

@router.get("/tts/poems")
async def get_poems_tts_status(
    page: int = 1,
    per_page: int = 20,
    filter: str = "all",  # all, with_tts, without_tts
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of poems with TTS status."""
    query = select(Poem, PoemTTSAudio).outerjoin(PoemTTSAudio)

    if filter == "with_tts":
        query = query.where(PoemTTSAudio.id != None)
    elif filter == "without_tts":
        query = query.where(PoemTTSAudio.id == None)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Get paginated results
    offset = (page - 1) * per_page
    result = await db.execute(query.offset(offset).limit(per_page))
    rows = result.all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if total > 0 else 1,
        "poems": [
            {
                "id": poem.id,
                "title": poem.title[:50] if poem.title else "Untitled",
                "has_tts": tts is not None,
                "tts_duration": tts.duration_seconds if tts else None,
                "tts_generated_at": tts.generated_at.isoformat() if tts and tts.generated_at else None
            }
            for poem, tts in rows
        ]
    }
