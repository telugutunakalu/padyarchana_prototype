#!/usr/bin/env python3
"""Batch-onboard the 33 cleaned wikibook JSONs into padyarchana.db in one session.
Uses skip_duplicate_check (fresh corpus, none of these sources exist yet) and lets
the poems_fts trigger maintain the FTS5 index. Run via ./venv/bin/python only."""
import asyncio
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)  # silence per-stmt echo

from app.database import AsyncSessionLocal, engine  # noqa: E402
from scripts.import_json import import_poems_from_json, ensure_tables_exist  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


async def main():
    keep = json.loads((ROOT / "crawlers" / "keep_list.json").read_text())
    await ensure_tables_exist()
    results = []
    async with AsyncSessionLocal() as db:
        for b in keep:
            fp = ROOT / "padyalu_json_data" / f"{b['slug']}.json"
            r = await import_poems_from_json(db, str(fp), skip_duplicate_check=True, batch_size=2000)
            results.append(r)
            print(f"  [{len(results):2d}/33] {r['imported']:5d}  {r['source']}", flush=True)
    await engine.dispose()
    print(f"\n=== ONBOARD COMPLETE: {sum(r['imported'] for r in results)} poems across {len(results)} works ===")


if __name__ == "__main__":
    asyncio.run(main())
