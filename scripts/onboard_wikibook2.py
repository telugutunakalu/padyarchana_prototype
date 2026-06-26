import asyncio, logging, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
from app.database import AsyncSessionLocal, engine
from scripts.import_json import import_poems_from_json, ensure_tables_exist
ROOT = Path(__file__).resolve().parent.parent
STAGE = ROOT / "crawlers" / "wikibook2_json"
JD = ROOT / "padyalu_json_data"

async def main():
    moved = []
    for f in sorted(STAGE.glob("*.json")):
        dest = JD / f.name
        shutil.move(str(f), str(dest)); moved.append(dest)
    print(f"moved {len(moved)} files to padyalu_json_data/", flush=True)
    await ensure_tables_exist()
    total = 0
    async with AsyncSessionLocal() as db:
        for i, fp in enumerate(moved, 1):
            r = await import_poems_from_json(db, str(fp), skip_duplicate_check=True, batch_size=2000)
            total += r["imported"]; print(f"  [{i:2d}/{len(moved)}] +{r['imported']:5d}  {fp.stem}", flush=True)
    await engine.dispose()
    print(f"\n=== ONBOARD COMPLETE: {total} padyalu across {len(moved)} books ===")

asyncio.run(main())
