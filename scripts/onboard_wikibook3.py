import asyncio, logging, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
from app.database import AsyncSessionLocal, engine
from scripts.import_json import import_poems_from_json, ensure_tables_exist
ROOT = Path(__file__).resolve().parent.parent
STAGE = ROOT / "crawlers" / "wikibook3_json"
JD = ROOT / "padyalu_json_data"
SKIP = {"saugamdhikaprasavaapaharanamu_gopaalaraaju",      # ద్విపద re-do (DB has it) — skip per user
        "shriinivaasavilaasasevadhi_vemkataarya",          # ద్విపద re-do (DB has it) — skip per user
        "shishupaalavadha_vemkatakavi"}                    # 96% already in DB — skip

async def main():
    moved = []
    for f in sorted(STAGE.glob("*.json")):
        if f.stem in SKIP:
            continue
        dest = JD / f.name
        shutil.move(str(f), str(dest)); moved.append(dest)
    print(f"moved {len(moved)} fresh books to padyalu_json_data/ (skipped {len(SKIP)})", flush=True)
    await ensure_tables_exist()
    total = skipped = 0
    async with AsyncSessionLocal() as db:
        for i, fp in enumerate(moved, 1):
            r = await import_poems_from_json(db, str(fp), skip_duplicate_check=False, batch_size=2000)
            total += r["imported"]; skipped += r.get("skipped", 0)
            print(f"  [{i:2d}/{len(moved)}] +{r['imported']:5d} (skip {r.get('skipped',0):4d})  {fp.stem[:44]}", flush=True)
    await engine.dispose()
    print(f"\n=== ONBOARD COMPLETE: {total} imported, {skipped} skipped (dupes), across {len(moved)} books ===")

asyncio.run(main())
