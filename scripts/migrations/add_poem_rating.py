#!/usr/bin/env python3
"""Add the poems.rating column (admin quality tag: gold|silver|bronze) + its index.

Idempotent. SQLAlchemy's create_all only creates missing TABLES, never adds a
column to an existing one, so the live DB needs this explicit ALTER. Run via
./venv/bin/python (the rating column itself isn't in the FTS surface, so this is
a plain DDL change — no poems_fts impact)."""
import sqlite3
import sys
from pathlib import Path


def apply(db_path: str | Path) -> dict:
    con = sqlite3.connect(str(db_path))
    try:
        cols = [r[1] for r in con.execute("PRAGMA table_info(poems)")]
        added = False
        if "rating" not in cols:
            con.execute("ALTER TABLE poems ADD COLUMN rating VARCHAR(20)")
            added = True
        con.execute("CREATE INDEX IF NOT EXISTS ix_poems_rating ON poems(rating)")
        con.commit()
        return {"column_added": added, "index_ensured": True}
    finally:
        con.close()


if __name__ == "__main__":
    db = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "padyarchana.db"
    print(f"applying add_poem_rating to {db} …")
    print(apply(db))
