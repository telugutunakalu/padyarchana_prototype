"""
TTS Service for on-demand and batch audio generation.
Uses Indic Parler-TTS for Telugu text-to-speech.
"""
import json
from datetime import datetime
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import soundfile as sf

from app.models import Poem, PoemTTSAudio, TTSBatchJob, JobStatus
from app.database import AsyncSessionLocal

# TTS Configuration
TTS_OUTPUT_DIR = Path("static/tts_audio")
VOICE_DESCRIPTION = "Lalitha speaks with a clear, expressive voice at a moderate pace. The recording is of very high quality with no background noise."


def _generate_tts_sync(text: str, output_path: Path) -> tuple[float, int]:
    """
    Synchronous TTS generation using Indic Parler-TTS.
    Returns (duration_seconds, file_size_bytes).
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "indic_tts"))
    from test_parler import generate_telugu_speech

    generate_telugu_speech(text, VOICE_DESCRIPTION, str(output_path))

    # Get file info
    file_size = output_path.stat().st_size
    audio_data, sample_rate = sf.read(str(output_path))
    duration = len(audio_data) / sample_rate

    return duration, file_size


async def get_tts_status(db: AsyncSession, poem_id: int) -> PoemTTSAudio | None:
    """Check if TTS audio exists for a poem."""
    result = await db.execute(
        select(PoemTTSAudio).where(PoemTTSAudio.poem_id == poem_id)
    )
    return result.scalar_one_or_none()


async def get_or_generate_tts(db: AsyncSession, poem_id: int) -> PoemTTSAudio | None:
    """Get existing TTS audio or generate on-demand."""
    # Check if TTS already exists
    tts = await get_tts_status(db, poem_id)
    if tts:
        return tts

    # Get poem
    result = await db.execute(select(Poem).where(Poem.id == poem_id))
    poem = result.scalar_one_or_none()
    if not poem:
        return None

    # Ensure output directory exists
    TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = TTS_OUTPUT_DIR / f"{poem_id}.wav"

    # Generate TTS (blocking - model loads on first call)
    duration, file_size = _generate_tts_sync(poem.text, output_path)

    # Save to database
    tts = PoemTTSAudio(
        poem_id=poem_id,
        filename=f"{poem_id}.wav",
        duration_seconds=duration,
        file_size_bytes=file_size,
        voice_description=VOICE_DESCRIPTION
    )
    db.add(tts)
    await db.commit()
    await db.refresh(tts)

    return tts


async def run_batch_tts_job(job_id: int, limit: int):
    """
    Background task to run batch TTS generation.
    This runs asynchronously and updates job status in database.
    """
    async with AsyncSessionLocal() as db:
        # Get job
        job = await db.get(TTSBatchJob, job_id)
        if not job:
            return

        job.status = JobStatus.RUNNING.value
        job.started_at = datetime.utcnow()
        await db.commit()

        try:
            # Get poems without TTS
            result = await db.execute(
                select(Poem)
                .outerjoin(PoemTTSAudio)
                .where(PoemTTSAudio.id == None)
                .limit(limit)
            )
            poems = result.scalars().all()

            errors = []
            for poem in poems:
                # Check if cancelled (refresh job state)
                await db.refresh(job)
                if job.status == JobStatus.CANCELLED.value:
                    break

                job.current_poem_id = poem.id
                await db.commit()

                try:
                    # Generate TTS for this poem
                    TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                    output_path = TTS_OUTPUT_DIR / f"{poem.id}.wav"

                    duration, file_size = _generate_tts_sync(poem.text, output_path)

                    # Save to database
                    tts = PoemTTSAudio(
                        poem_id=poem.id,
                        filename=f"{poem.id}.wav",
                        duration_seconds=duration,
                        file_size_bytes=file_size,
                        voice_description=VOICE_DESCRIPTION
                    )
                    db.add(tts)
                    await db.commit()

                    job.completed_poems += 1
                except Exception as e:
                    job.failed_poems += 1
                    errors.append({"poem_id": poem.id, "error": str(e)})

                await db.commit()

            # Mark job as completed
            if job.status != JobStatus.CANCELLED.value:
                job.status = JobStatus.COMPLETED.value
            job.completed_at = datetime.utcnow()
            job.error_log = json.dumps(errors) if errors else None
            job.current_poem_id = None
            await db.commit()

        except Exception as e:
            job.status = JobStatus.FAILED.value
            job.error_log = str(e)
            job.completed_at = datetime.utcnow()
            await db.commit()
