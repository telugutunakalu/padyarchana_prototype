#!/usr/bin/env python3
"""Batch-onboard the 9 online_padyalu JSON files (శంకరాభరణం blog, ~118k padyalu,
poet=unknown, category 'online padyalu') into padyarchana.db in one session.
Fresh corpus → skip_duplicate_check. Run via ./venv/bin/python only."""
import asyncio
import glob
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from app.database import AsyncSessionLocal, engine  # noqa: E402
from scripts.import_json import import_poems_from_json, ensure_tables_exist  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


async def main():
    files = sorted(glob.glob(str(ROOT / "padyalu_json_data" / "online_padyalu_*.json")))
    print(f"onboarding {len(files)} online_padyalu files…", flush=True)
    await ensure_tables_exist()
    total = 0
    async with AsyncSessionLocal() as db:
        for i, fp in enumerate(files, 1):
            r = await import_poems_from_json(db, fp, skip_duplicate_check=True, batch_size=3000)
            total += r["imported"]
            print(f"  [{i}/{len(files)}] {r['imported']:6d}  {Path(fp).name}", flush=True)
    await engine.dispose()
    print(f"\n=== ONBOARD COMPLETE: {total} online padyalu across {len(files)} files ===")


if __name__ == "__main__":
    asyncio.run(main())
