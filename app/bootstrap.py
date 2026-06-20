"""
First-run DB bootstrap.

When the app starts and `poems` is empty, populate it from `seed.sql`
(meters + poets) and `padyalu_json_data/*.json` (poems), then build the
FTS5 search index. Idempotent — does nothing once `poems` has rows.

This is invoked from `app.main`'s lifespan handler, right after
SQLAlchemy's `Base.metadata.create_all` has created the regular tables.

Notes:
  - We deliberately do NOT execute schema.sql; SQLAlchemy already
    creates the regular tables from the ORM models. schema.sql is kept
    as a dump artefact for inspection / external-tool restore, but the
    canonical schema source remains the Python models.
  - The FTS5 virtual table + sync triggers are set up via the standalone
    `scripts/setup_fts5_search.py` migration, which is FTS5-capable
    because it goes through Python's sqlite3 module (the system CLI is
    too old for FTS5 on this box).
"""
from __future__ import annotations

import asyncio
import sqlite3
import time
from pathlib import Path

from sqlalchemy import select, func, text

from app.config import settings
from app.database import AsyncSessionLocal
from app.models import Poem


_PROJECT_ROOT = Path(__file__).parent.parent
_DATA_DIR = _PROJECT_ROOT / "padyalu_json_data"
_SEED_SQL = _PROJECT_ROOT / "seed.sql"
_DB_FILE = _PROJECT_ROOT / "padyarchana.db"


def _log(msg: str) -> None:
    print(f"[bootstrap] {msg}", flush=True)


async def _poems_count() -> int:
    async with AsyncSessionLocal() as db:
        n = await db.scalar(select(func.count(Poem.id)))
    return n or 0


def _has_fts5_table(db_path: Path) -> bool:
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='poems_fts'"
        ).fetchone()
        return row is not None
    finally:
        con.close()


def _apply_seed_sync(db_path: Path) -> None:
    """Apply seed.sql (meters + poets reference rows) via raw sqlite3."""
    if not _SEED_SQL.exists():
        _log(f"seed.sql not found at {_SEED_SQL} — skipping reference data seed")
        return
    sql = _SEED_SQL.read_text(encoding="utf-8")
    con = sqlite3.connect(db_path)
    try:
        # seed.sql wraps its INSERTs in a BEGIN/COMMIT — fine to executescript.
        con.executescript(sql)
        con.commit()
    finally:
        con.close()


async def _import_corpus() -> int:
    """Run scripts.import_json.import_poems_from_json over every
    padyalu_json_data/*.json. Returns total imported."""
    # Imported lazily so a fresh checkout without scripts/ still loads
    # this module without ImportError.
    from scripts.import_json import import_poems_from_json

    files = sorted(_DATA_DIR.glob("*.json"))
    total_imported = 0
    _log(f"importing {len(files)} corpus files from {_DATA_DIR}")
    async with AsyncSessionLocal() as db:
        for path in files:
            try:
                result = await import_poems_from_json(
                    db,
                    str(path),
                    skip_duplicate_check=True,
                    batch_size=1000,
                )
                n = result.get("imported", 0) if isinstance(result, dict) else 0
                total_imported += n
            except Exception as e:
                _log(f"  {path.name}: ERROR — {e}")
    return total_imported


def _ensure_fts5_sync(db_path: Path) -> None:
    """Create poems_fts + triggers if absent, then rebuild the index."""
    # Defer to the dedicated migration script — it's already idempotent
    # and handles the search_text backfill / FTS index rebuild.
    from scripts.setup_fts5_search import main as fts5_setup
    fts5_setup()


async def auto_bootstrap_if_empty(db_file_existed_before_init: bool) -> None:
    """Idempotent first-run bootstrap.

    Triggers ONLY when the padyarchana.db file did not exist before the
    app started (i.e., truly a fresh clone or a deliberately-cleared
    on-disk state). Once the DB file is present, we never auto-rebuild
    — that respects an admin who deliberately empties tables for
    testing without trampling on their work.
    """
    if db_file_existed_before_init:
        return

    # Belt-and-braces double-check: if somehow poems already has data
    # (e.g., concurrent init), bail.
    if await _poems_count() > 0:
        return

    if not _DATA_DIR.is_dir():
        _log(f"corpus dir {_DATA_DIR} missing — skipping bootstrap")
        return

    _log("fresh DB file detected — running first-run bootstrap")
    t0 = time.perf_counter()

    loop = asyncio.get_event_loop()

    # 1. Reference data (meters + poets). Synchronous via sqlite3 since
    #    seed.sql is a plain SQL dump.
    _log("applying seed.sql (meters + poets)…")
    try:
        await loop.run_in_executor(None, _apply_seed_sync, _DB_FILE)
    except Exception as e:
        _log(f"  seed.sql failed — {e}; continuing (importer will create rows as needed)")

    # 2. Corpus import (poems).
    total = await _import_corpus()
    _log(f"corpus import done — {total:,} poems")

    # 3. FTS5 setup (virtual table, triggers, search_text backfill, index rebuild).
    if not _has_fts5_table(_DB_FILE):
        _log("setting up FTS5 trigram index…")
    else:
        _log("FTS5 already present — refreshing search_text + index…")
    try:
        await loop.run_in_executor(None, _ensure_fts5_sync, _DB_FILE)
    except Exception as e:
        _log(f"  FTS5 setup failed — {e}; the app will fall back to ilike search")

    elapsed = time.perf_counter() - t0
    final_n = await _poems_count()
    _log(f"bootstrap complete in {elapsed:.1f}s — DB now has {final_n:,} poems")
