"""
API endpoints for audio file management and annotations.
"""
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.auth import require_admin
from app.config import settings
from app.database import get_db
from app.models import Poem, PoemAudio, AudioAnnotation
from app.schemas.audio import (
    AudioMetadataResponse,
    AnnotationCreate,
    AnnotationResponse,
    AnnotationBatchCreate,
)

router = APIRouter()


def get_audio_duration(file_path: Path) -> Optional[float]:
    """Get audio duration using mutagen library if available."""
    try:
        from mutagen.mp3 import MP3
        from mutagen.wave import WAVE

        suffix = file_path.suffix.lower()
        if suffix == ".mp3":
            audio = MP3(str(file_path))
            return audio.info.length
        elif suffix == ".wav":
            audio = WAVE(str(file_path))
            return audio.info.length
    except ImportError:
        # mutagen not installed, skip duration extraction
        pass
    except Exception:
        pass
    return None


@router.post("/poems/{poem_id}/audio", response_model=AudioMetadataResponse)
async def upload_audio(
    poem_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _admin = Depends(require_admin),
):
    """Upload an audio file for a poem."""
    # Verify poem exists
    result = await db.execute(select(Poem).where(Poem.id == poem_id))
    poem = result.scalar_one_or_none()
    if not poem:
        raise HTTPException(status_code=404, detail="Poem not found")

    # Validate file format
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if file_ext not in settings.ALLOWED_AUDIO_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format. Allowed formats: {', '.join(settings.ALLOWED_AUDIO_FORMATS)}"
        )

    # Read file content and check size
    content = await file.read()
    if len(content) > settings.MAX_AUDIO_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_AUDIO_FILE_SIZE // (1024*1024)}MB"
        )

    # Create directory for this poem's audio
    poem_audio_dir = settings.settings.AUDIO_DIR / str(poem_id)
    poem_audio_dir.mkdir(parents=True, exist_ok=True)

    # Check if audio already exists for this poem - delete old file if so
    existing_result = await db.execute(
        select(PoemAudio).where(PoemAudio.poem_id == poem_id)
    )
    existing_audio = existing_result.scalar_one_or_none()
    if existing_audio:
        # Delete old file
        old_file_path = poem_audio_dir / existing_audio.filename
        if old_file_path.exists():
            old_file_path.unlink()
        # Delete old database record
        await db.delete(existing_audio)
        await db.commit()

    # Save the new file
    filename = f"audio.{file_ext}"
    file_path = poem_audio_dir / filename

    with open(file_path, "wb") as f:
        f.write(content)

    # Get audio duration if possible
    duration = get_audio_duration(file_path)

    # Create database record
    db_audio = PoemAudio(
        poem_id=poem_id,
        filename=filename,
        original_filename=file.filename,
        duration_seconds=duration,
        format=file_ext,
        file_size_bytes=len(content)
    )
    db.add(db_audio)
    await db.commit()
    await db.refresh(db_audio)

    # Return response with audio URL
    return AudioMetadataResponse(
        id=db_audio.id,
        poem_id=db_audio.poem_id,
        filename=db_audio.filename,
        original_filename=db_audio.original_filename,
        duration_seconds=db_audio.duration_seconds,
        format=db_audio.format,
        file_size_bytes=db_audio.file_size_bytes,
        uploaded_at=db_audio.uploaded_at,
        audio_url=f"/static/audio/poems/{poem_id}/{filename}"
    )


@router.get("/poems/{poem_id}/audio", response_model=AudioMetadataResponse)
async def get_audio_metadata(poem_id: int, db: AsyncSession = Depends(get_db)):
    """Get audio metadata for a poem."""
    result = await db.execute(
        select(PoemAudio).where(PoemAudio.poem_id == poem_id)
    )
    audio = result.scalar_one_or_none()

    if not audio:
        raise HTTPException(status_code=404, detail="No audio found for this poem")

    return AudioMetadataResponse(
        id=audio.id,
        poem_id=audio.poem_id,
        filename=audio.filename,
        original_filename=audio.original_filename,
        duration_seconds=audio.duration_seconds,
        format=audio.format,
        file_size_bytes=audio.file_size_bytes,
        uploaded_at=audio.uploaded_at,
        audio_url=f"/static/audio/poems/{poem_id}/{audio.filename}"
    )


@router.delete("/poems/{poem_id}/audio", status_code=204)
async def delete_audio(
    poem_id: int,
    db: AsyncSession = Depends(get_db),
    _admin = Depends(require_admin),
):
    """Delete audio file for a poem."""
    result = await db.execute(
        select(PoemAudio).where(PoemAudio.poem_id == poem_id)
    )
    audio = result.scalar_one_or_none()

    if not audio:
        raise HTTPException(status_code=404, detail="No audio found for this poem")

    # Delete file from filesystem
    file_path = settings.AUDIO_DIR / str(poem_id) / audio.filename
    if file_path.exists():
        file_path.unlink()

    # Try to remove the directory if empty
    poem_dir = settings.AUDIO_DIR / str(poem_id)
    if poem_dir.exists() and not any(poem_dir.iterdir()):
        poem_dir.rmdir()

    # Delete database record (cascades to annotations)
    await db.delete(audio)
    await db.commit()

    return None


@router.get("/poems/{poem_id}/annotations", response_model=List[AnnotationResponse])
async def get_annotations(poem_id: int, db: AsyncSession = Depends(get_db)):
    """Get all annotations for a poem's audio."""
    # First verify audio exists
    audio_result = await db.execute(
        select(PoemAudio).where(PoemAudio.poem_id == poem_id)
    )
    audio = audio_result.scalar_one_or_none()

    if not audio:
        raise HTTPException(status_code=404, detail="No audio found for this poem")

    # Get annotations
    result = await db.execute(
        select(AudioAnnotation)
        .where(AudioAnnotation.poem_audio_id == audio.id)
        .order_by(AudioAnnotation.word_index)
    )
    annotations = result.scalars().all()

    return annotations


@router.post("/poems/{poem_id}/annotations", response_model=List[AnnotationResponse])
async def save_annotations(
    poem_id: int,
    batch: AnnotationBatchCreate,
    db: AsyncSession = Depends(get_db),
    _admin = Depends(require_admin),
):
    """Save or update annotations for a poem's audio (batch operation)."""
    # First verify audio exists
    audio_result = await db.execute(
        select(PoemAudio).where(PoemAudio.poem_id == poem_id)
    )
    audio = audio_result.scalar_one_or_none()

    if not audio:
        raise HTTPException(status_code=404, detail="No audio found for this poem")

    # Delete existing annotations for this audio
    await db.execute(
        delete(AudioAnnotation).where(AudioAnnotation.poem_audio_id == audio.id)
    )

    # Create new annotations
    new_annotations = []
    for ann in batch.annotations:
        db_annotation = AudioAnnotation(
            poem_audio_id=audio.id,
            word_index=ann.word_index,
            word_text=ann.word_text,
            timestamp_ms=ann.timestamp_ms,
            flags=ann.flags
        )
        db.add(db_annotation)
        new_annotations.append(db_annotation)

    await db.commit()

    # Refresh to get IDs
    for ann in new_annotations:
        await db.refresh(ann)

    return new_annotations


@router.delete("/poems/{poem_id}/annotations", status_code=204)
async def clear_annotations(
    poem_id: int,
    db: AsyncSession = Depends(get_db),
    _admin = Depends(require_admin),
):
    """Clear all annotations for a poem's audio."""
    # First verify audio exists
    audio_result = await db.execute(
        select(PoemAudio).where(PoemAudio.poem_id == poem_id)
    )
    audio = audio_result.scalar_one_or_none()

    if not audio:
        raise HTTPException(status_code=404, detail="No audio found for this poem")

    # Delete all annotations
    await db.execute(
        delete(AudioAnnotation).where(AudioAnnotation.poem_audio_id == audio.id)
    )
    await db.commit()

    return None
