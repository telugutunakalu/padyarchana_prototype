"""
Import poems from a JSON file into the database.
This script adds new data without dropping existing tables.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import engine, Base, AsyncSessionLocal
from app.models import Poet, Meter, Poem
from app.utils.search_text import build_search_text


async def load_json_data(file_path: str) -> dict:
    """Load JSON data from file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


async def create_or_get_poet(db: AsyncSession, poet_name: str, era: str = None) -> Poet:
    """Create poet if doesn't exist, otherwise return existing."""
    result = await db.execute(select(Poet).where(Poet.name == poet_name))
    poet = result.scalar_one_or_none()

    if not poet:
        poet = Poet(name=poet_name, era=era)
        db.add(poet)
        await db.flush()
        print(f"  Created poet: {poet_name}")
    else:
        print(f"  Found existing poet: {poet_name}")

    return poet


async def create_or_get_meter(db: AsyncSession, meter_name: str, description: str = None) -> Meter:
    """Create meter if doesn't exist, otherwise return existing."""
    result = await db.execute(select(Meter).where(Meter.name == meter_name))
    meter = result.scalar_one_or_none()

    if not meter:
        meter = Meter(name=meter_name, description=description)
        db.add(meter)
        await db.flush()
        print(f"  Created meter: {meter_name}")
    else:
        print(f"  Found existing meter: {meter_name}")

    return meter


async def check_poem_exists(db: AsyncSession, poem_text: str, poet_id: int) -> bool:
    """Check if a poem with the same text and poet already exists."""
    result = await db.execute(
        select(Poem).where(Poem.text == poem_text, Poem.poet_id == poet_id)
    )
    return result.scalar_one_or_none() is not None


async def import_poems_from_json(
    db: AsyncSession,
    file_path: str,
    default_meter_name: str = "Unknown",
    literary_form: str = "శతకం",
    data: dict = None,
    skip_duplicate_check: bool = False,
    batch_size: int = 1000,
):
    """Import poems from a JSON file or pre-loaded data dict."""
    print(f"\n{'='*60}")
    print(f"Loading data from: {file_path}")
    print(f"{'='*60}")

    if data is None:
        data = await load_json_data(file_path)

    # Get source name from JSON
    source_name = data.get("shatakam_title_telugu") or Path(file_path).stem
    print(f"\nSource: {source_name}")

    # Get or create poet
    poet_name = data.get("author_telugu") or "Unknown"
    year = data.get("year")
    era = f"{year}" if year else None
    poet = await create_or_get_poet(db, poet_name, era)

    # File-level literary form override (e.g. ద్విపదకావ్యం)
    file_literary_form = data.get("literary_form_telugu") or literary_form

    # File-level meter override (used when individual poems don't specify Chandassu)
    file_meter_name = data.get("meter_telugu") or default_meter_name
    default_meter = await create_or_get_meter(
        db,
        file_meter_name,
        "Meter not specified - requires classification" if file_meter_name == "Unknown" else None,
    )

    # Process each poem
    poems_data = data.get("poems", [])
    print(f"\nProcessing {len(poems_data)} poems (skip_duplicate_check={skip_duplicate_check}, batch_size={batch_size})...")

    imported_count = 0
    skipped_count = 0
    pending_in_batch = 0

    for poem_data in poems_data:
        # Get lines
        lines = poem_data.get("lines_telugu", [])
        poem_text = "\n".join(lines)

        # Skip if poem already exists (unless caller opts out for fresh corpora)
        if not skip_duplicate_check and await check_poem_exists(db, poem_text, poet.id):
            skipped_count += 1
            continue

        # Get title — include kanda/chapter when present for human readability
        # and to avoid collisions (couplet_number can restart per chapter).
        # 'ch' prefix is only used when chapter is purely numeric; for Telugu
        # chapter names (e.g. 'ప్రథమాశ్వాసము'), use the name bare.
        poem_id = poem_data.get("id", imported_count + 1)
        kanda = poem_data.get("kanda")
        chapter = poem_data.get("chapter")
        parts = [source_name]
        if kanda:
            parts.append(kanda)
        if chapter:
            chapter_str = str(chapter).strip()
            is_numeric = bool(chapter_str) and all(
                ch.isdigit() or ch == "." for ch in chapter_str
            )
            parts.append(f"ch{chapter_str}" if is_numeric else chapter_str)
        parts.append(f"c{poem_id}" if (kanda or chapter) else str(poem_id))
        title = " - ".join(parts)

        # Get meter/chandassu if specified
        meter_name = poem_data.get("Chandassu") or poem_data.get("chandassu")
        if meter_name:
            meter = await create_or_get_meter(db, meter_name)
        else:
            meter = default_meter

        # Build search_text (concatenated surface for the FTS5 trigram index).
        # Uses the shared helper so admin edits via PUT /api/poems/{id} land
        # in the FTS surface the same way fresh imports do.
        prathi = poem_data.get("prathipadartham")
        bhavam = poem_data.get("bhavam")
        search_text = build_search_text(title[:500], poem_text, bhavam, prathi)

        # Create poem
        poem = Poem(
            title=title[:500],
            text=poem_text,
            source=source_name,
            kanda=kanda,
            poet_id=poet.id,
            meter_id=meter.id,
            line_count=len(lines),
            word_count=len(poem_text.split()),
            literary_form=file_literary_form,
            prathipadartham=prathi,
            bhavam=bhavam,
            search_text=search_text,
        )

        db.add(poem)
        imported_count += 1
        pending_in_batch += 1

        if pending_in_batch >= batch_size:
            await db.flush()
            pending_in_batch = 0

    await db.commit()

    print(f"\n{'='*60}")
    print(f"Import Summary:")
    print(f"  - Imported: {imported_count} poems")
    print(f"  - Skipped (duplicates): {skipped_count} poems")
    print(f"  - Source: {source_name}")
    print(f"  - Poet: {poet_name}")
    print(f"  - Default Meter: {default_meter_name}")
    print(f"{'='*60}")

    return {
        "file": str(file_path),
        "source": source_name,
        "poet": poet_name,
        "imported": imported_count,
        "skipped": skipped_count,
        "total_in_file": len(poems_data),
    }


async def ensure_tables_exist():
    """Ensure database tables exist without dropping data."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables verified.")


async def main():
    """Main import function."""
    import argparse

    parser = argparse.ArgumentParser(description="Import poems from a padyalu_json_data JSON file.")
    parser.add_argument("json_file", nargs="?", default="padyalu_json_data/abhinava_sumathi_satakam.json")
    parser.add_argument("--skip-duplicate-check", action="store_true",
                        help="Skip the per-poem duplicate check (use for fresh corpus imports — much faster).")
    parser.add_argument("--batch-size", type=int, default=1000,
                        help="Flush to DB every N inserts (default 1000).")
    parser.add_argument("--default-meter", default="Unknown",
                        help="Meter name to use when neither file nor poem specifies one.")
    args = parser.parse_args()

    file_path = Path(__file__).parent.parent / args.json_file

    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    print("\n" + "="*60)
    print("  పద్యార్చన (Padyarchana) - JSON Importer")
    print("="*60)

    # Ensure tables exist
    await ensure_tables_exist()

    # Import data
    async with AsyncSessionLocal() as db:
        try:
            await import_poems_from_json(
                db,
                str(file_path),
                default_meter_name=args.default_meter,
                skip_duplicate_check=args.skip_duplicate_check,
                batch_size=args.batch_size,
            )
            print("\nImport completed successfully!")
        except Exception as e:
            print(f"\nError during import: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
            raise
        finally:
            await db.close()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
