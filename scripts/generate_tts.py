"""
Batch TTS generation script for Padyarchana.
Generates TTS audio for poems without existing TTS files.

Usage:
    python scripts/generate_tts.py           # Generate first 20 poems
    python scripts/generate_tts.py --limit 50  # Generate first 50 poems
    python scripts/generate_tts.py --all     # Generate all remaining poems
"""
import asyncio
import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
import soundfile as sf

from app.database import AsyncSessionLocal
from app.models import Poem, PoemTTSAudio

# TTS Configuration
TTS_OUTPUT_DIR = Path(__file__).parent.parent / "static" / "tts_audio"
VOICE_DESCRIPTION = "Lalitha speaks with a clear, expressive voice at a moderate pace. The recording is of very high quality with no background noise."


def generate_tts_audio(text: str, output_path: Path) -> tuple[float, int]:
    """
    Generate TTS audio using Indic Parler-TTS.
    Returns (duration_seconds, file_size_bytes).
    """
    # Import TTS function from indic_tts
    indic_tts_path = Path(__file__).parent.parent / "indic_tts"
    sys.path.insert(0, str(indic_tts_path))
    from test_parler import generate_telugu_speech

    generate_telugu_speech(text, VOICE_DESCRIPTION, str(output_path))

    # Get file info
    file_size = output_path.stat().st_size
    audio_data, sample_rate = sf.read(str(output_path))
    duration = len(audio_data) / sample_rate

    return duration, file_size


async def generate_tts_batch(limit: int = 20, generate_all: bool = False):
    """Generate TTS for poems without existing TTS audio."""
    print("=" * 60)
    print("  TTS Batch Generation - Padyarchana")
    print("=" * 60)

    # Ensure output directory exists
    TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput directory: {TTS_OUTPUT_DIR}")

    async with AsyncSessionLocal() as db:
        # Count poems without TTS
        result = await db.execute(
            select(Poem)
            .outerjoin(PoemTTSAudio)
            .where(PoemTTSAudio.id == None)
        )
        all_poems_without_tts = result.scalars().all()
        total_without_tts = len(all_poems_without_tts)

        print(f"Poems without TTS: {total_without_tts}")

        if total_without_tts == 0:
            print("\nAll poems already have TTS audio!")
            return

        # Determine how many to process
        if generate_all:
            poems_to_process = all_poems_without_tts
            print(f"Processing ALL {total_without_tts} poems")
        else:
            poems_to_process = all_poems_without_tts[:limit]
            print(f"Processing first {len(poems_to_process)} poems (limit: {limit})")

        print("-" * 60)

        # Process each poem
        success_count = 0
        error_count = 0

        for i, poem in enumerate(poems_to_process):
            print(f"\n[{i + 1}/{len(poems_to_process)}] Poem ID: {poem.id}")
            print(f"    Title: {poem.title[:50]}...")

            output_path = TTS_OUTPUT_DIR / f"{poem.id}.wav"

            try:
                # Generate TTS
                print("    Generating audio...")
                duration, file_size = generate_tts_audio(poem.text, output_path)

                # Create database record
                tts_record = PoemTTSAudio(
                    poem_id=poem.id,
                    filename=f"{poem.id}.wav",
                    duration_seconds=duration,
                    file_size_bytes=file_size,
                    voice_description=VOICE_DESCRIPTION
                )
                db.add(tts_record)
                await db.commit()

                print(f"    Success: {duration:.1f}s, {file_size / 1024:.1f}KB")
                success_count += 1

            except Exception as e:
                print(f"    Error: {e}")
                error_count += 1
                # Remove partial file if it exists
                if output_path.exists():
                    output_path.unlink()

        # Summary
        print("\n" + "=" * 60)
        print("  Generation Summary")
        print("=" * 60)
        print(f"  Successful: {success_count}")
        print(f"  Errors: {error_count}")
        print(f"  Remaining: {total_without_tts - success_count}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Generate TTS audio for poems")
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=20,
        help="Number of poems to process (default: 20)"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        dest="generate_all",
        help="Generate TTS for ALL remaining poems"
    )

    args = parser.parse_args()

    asyncio.run(generate_tts_batch(
        limit=args.limit,
        generate_all=args.generate_all
    ))


if __name__ == "__main__":
    main()
