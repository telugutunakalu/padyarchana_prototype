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
    default_meter_name: str = "Unknown"
):
    """Import poems from a JSON file."""
    print(f"\n{'='*60}")
    print(f"Loading data from: {file_path}")
    print(f"{'='*60}")

    data = await load_json_data(file_path)

    # Get source name from JSON
    source_name = data.get("shatakam_title_telugu") or Path(file_path).stem
    print(f"\nSource: {source_name}")

    # Get or create poet
    poet_name = data.get("author_telugu") or "Unknown"
    year = data.get("year")
    era = f"{year}" if year else None
    poet = await create_or_get_poet(db, poet_name, era)

    # Get or create default meter for poems without chandassu
    default_meter = await create_or_get_meter(
        db,
        default_meter_name,
        "Meter not specified - requires classification"
    )

    # Process each poem
    poems_data = data.get("poems", [])
    print(f"\nProcessing {len(poems_data)} poems...")

    imported_count = 0
    skipped_count = 0

    for poem_data in poems_data:
        # Get lines
        lines = poem_data.get("lines_telugu", [])
        poem_text = "\n".join(lines)

        # Skip if poem already exists
        if await check_poem_exists(db, poem_text, poet.id):
            skipped_count += 1
            continue

        # Get title (using first line)
        poem_id = poem_data.get("id", imported_count + 1)
        title = f"{source_name} - {poem_id}"

        # Get meter/chandassu if specified
        meter_name = poem_data.get("Chandassu") or poem_data.get("chandassu")
        if meter_name:
            meter = await create_or_get_meter(db, meter_name)
        else:
            meter = default_meter

        # Create poem
        poem = Poem(
            title=title[:500],
            text=poem_text,
            source=source_name,
            poet_id=poet.id,
            meter_id=meter.id,
            line_count=len(lines),
            word_count=len(poem_text.split()),
            literary_form="శతకం"  # Shatakam form
        )

        db.add(poem)
        imported_count += 1

    await db.commit()

    print(f"\n{'='*60}")
    print(f"Import Summary:")
    print(f"  - Imported: {imported_count} poems")
    print(f"  - Skipped (duplicates): {skipped_count} poems")
    print(f"  - Source: {source_name}")
    print(f"  - Poet: {poet_name}")
    print(f"  - Default Meter: {default_meter_name}")
    print(f"{'='*60}")

    return imported_count


async def ensure_tables_exist():
    """Ensure database tables exist without dropping data."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables verified.")


async def main():
    """Main import function."""
    # Get JSON file from command line or use default
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        json_file = "padyalu_json_data/abhinava_sumathi_satakam.json"

    file_path = Path(__file__).parent.parent / json_file

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
            await import_poems_from_json(db, str(file_path), default_meter_name="Unknown")
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
