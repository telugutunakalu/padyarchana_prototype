"""
Seed database with initial data from JSON files.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import engine, Base, AsyncSessionLocal
from app.models import Poet, Meter, Poem


async def load_json_data(file_path: str) -> dict:
    """Load JSON data from file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


async def create_or_get_poet(db: AsyncSession, poet_name: str) -> Poet:
    """Create poet if doesn't exist, otherwise return existing."""
    from sqlalchemy import select

    result = await db.execute(select(Poet).where(Poet.name == poet_name))
    poet = result.scalar_one_or_none()

    if not poet:
        poet = Poet(name=poet_name)
        db.add(poet)
        await db.flush()
        print(f"Created poet: {poet_name}")
    else:
        print(f"Found existing poet: {poet_name}")

    return poet


async def create_or_get_meter(db: AsyncSession, meter_name: str) -> Meter:
    """Create meter if doesn't exist, otherwise return existing."""
    from sqlalchemy import select

    result = await db.execute(select(Meter).where(Meter.name == meter_name))
    meter = result.scalar_one_or_none()

    if not meter:
        meter = Meter(name=meter_name)
        db.add(meter)
        await db.flush()
        print(f"Created meter: {meter_name}")
    else:
        print(f"Found existing meter: {meter_name}")

    return meter


async def import_poems_from_json(db: AsyncSession, file_path: str):
    """Import poems from a JSON file."""
    print(f"\n📖 Loading data from {file_path}...")

    data = await load_json_data(file_path)

    # Get or create poet
    poet_name = data.get("author_telugu") or "Unknown"
    poet = await create_or_get_poet(db, poet_name)

    # Process each poem
    poems_data = data.get("poems", [])
    print(f"\n📝 Processing {len(poems_data)} poems...")

    for poem_data in poems_data:
        # Get lines
        lines = poem_data.get("lines_telugu", [])
        poem_text = "\n".join(lines)

        # Get title (using first line or makutam)
        title = lines[0] if lines else poem_data.get("makutam_telugu", "Untitled")

        # Get meter/chandassu
        meter_name = poem_data.get("Chandassu") or poem_data.get("chandassu")
        meter = None
        if meter_name:
            meter = await create_or_get_meter(db, meter_name)

        # Create poem
        poem = Poem(
            title=title[:500],  # Limit to 500 chars
            text=poem_text,
            poet_id=poet.id,
            meter_id=meter.id if meter else None,
            line_count=len(lines),
            word_count=len(poem_text.split()),
        )

        db.add(poem)

    await db.commit()
    print(f"✅ Successfully imported {len(poems_data)} poems from {file_path}")


async def seed_database():
    """Main function to seed the database."""
    print("🚀 Starting database seeding...")

    # Create tables
    print("\n📋 Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created")

    # Create session
    async with AsyncSessionLocal() as db:
        try:
            # Define JSON file paths
            json_files = [
                "padyalu_json_data/vemana_100.json",
                "padyalu_json_data/sumathii_satakam.json",
            ]

            # Import data from each file
            for json_file in json_files:
                file_path = Path(__file__).parent.parent / json_file
                if file_path.exists():
                    await import_poems_from_json(db, str(file_path))
                else:
                    print(f"⚠️  Warning: File not found: {json_file}")

            print("\n✅ Database seeding completed successfully!")
            print(f"\n📊 Summary:")
            print(f"   - Poets created")
            print(f"   - Meters created")
            print(f"   - Poems imported")

        except Exception as e:
            print(f"\n❌ Error during seeding: {e}")
            import traceback

            traceback.print_exc()
            await db.rollback()
            raise
        finally:
            await db.close()

    await engine.dispose()


if __name__ == "__main__":
    print("=" * 60)
    print("  పద్యార్చన (Padyarchana) - Database Seeder")
    print("=" * 60)

    asyncio.run(seed_database())

    print("\n" + "=" * 60)
    print("  Seeding Complete!")
    print("=" * 60)
