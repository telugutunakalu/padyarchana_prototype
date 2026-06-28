#!/usr/bin/env python3
"""Onboard the 4 దార్ల (vrdarla.blogspot.com) staging JSONs — 1195 four-line
padyalu (862 blog + 3 śatakams) under the NEW poet దార్ల వెంకటేశ్వరరావు.
Fresh corpus (new poet) → skip_duplicate_check. Run via ./venv/bin/python only
(system sqlite3 lacks FTS5; see memory db-sqlite3-cli-fts5)."""
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from app.database import AsyncSessionLocal, engine  # noqa: E402
from scripts.import_json import import_poems_from_json, ensure_tables_exist  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FILES = [
    "darla_blog_padyalu.json",
    "darla_mata_satakam.json",
    "darla_sisuvu_satakamu.json",
    "darla_kavula_dhanya_charita_satakam.json",
]


async def main():
    await ensure_tables_exist()
    total = 0
    async with AsyncSessionLocal() as db:
        for i, name in enumerate(FILES, 1):
            fp = ROOT / "padyalu_json_data" / name
            r = await import_poems_from_json(db, str(fp), skip_duplicate_check=True,
                                             batch_size=2000)
            total += r["imported"]
            print(f"  [{i}/{len(FILES)}] {r['imported']:5d}  {name}", flush=True)
    await engine.dispose()
    print(f"\n=== ONBOARD COMPLETE: {total} దార్ల padyalu across {len(FILES)} files ===")


if __name__ == "__main__":
    asyncio.run(main())
