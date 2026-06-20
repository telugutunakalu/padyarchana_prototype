"""
One-time migration that adds full-text search to padyarchana.

Steps:
  1. ALTER TABLE poems ADD COLUMN search_text TEXT  (nullable)
  2. Backfill search_text for all existing rows by concatenating
     title + text + bhavam + flattened prathipadartham (word + meaning).
  3. CREATE VIRTUAL TABLE poems_fts using FTS5 trigram tokenizer,
     with content='poems' and content_rowid='id' (no data duplication).
  4. Rebuild the FTS index from search_text.
  5. CREATE TRIGGERs to keep poems_fts in sync on insert/update/delete.

Idempotent: re-running won't add the column or triggers a second time.

Note: we must run all FTS operations through python's sqlite3 (3.45+); the
system sqlite3 CLI on this box is 3.13 and doesn't support FTS5 trigram.
"""
import json
import sqlite3
import time
from pathlib import Path

DB = Path(__file__).parent.parent / "padyarchana.db"
BATCH = 5000


def column_exists(con, table, col):
    return any(r[1] == col for r in con.execute(f"PRAGMA table_info({table})"))


def table_exists(con, name):
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name=?",
        (name,),
    ).fetchone() is not None


def build_search_text(title, text, bhavam, prathipadartham_json):
    """Flatten one poem's searchable surface into a single TEXT blob."""
    parts = []
    if title:   parts.append(title)
    if text:    parts.append(text)
    if bhavam:  parts.append(bhavam)
    if prathipadartham_json:
        try:
            entries = json.loads(prathipadartham_json) if isinstance(prathipadartham_json, str) else prathipadartham_json
        except Exception:
            entries = None
        if entries:
            for e in entries:
                w = e.get("word")
                m = e.get("meaning")
                if w: parts.append(w)
                if m: parts.append(m)
    return "\n".join(parts) if parts else None


def main():
    con = sqlite3.connect(DB)
    con.execute("PRAGMA cache_size = -128000")  # 128MB cache for the bulk update
    con.execute("PRAGMA synchronous = NORMAL")
    cur = con.cursor()

    # 1. ALTER TABLE — only if needed.
    if not column_exists(con, "poems", "search_text"):
        print("Adding poems.search_text column …")
        cur.execute("ALTER TABLE poems ADD COLUMN search_text TEXT")
        con.commit()
    else:
        print("poems.search_text already exists — skipping ALTER")

    # 2. Backfill search_text for rows that currently have it NULL.
    total = cur.execute("SELECT COUNT(*) FROM poems WHERE search_text IS NULL").fetchone()[0]
    print(f"Backfilling search_text for {total:,} rows …")
    if total:
        t0 = time.perf_counter()
        offset = 0
        processed = 0
        while True:
            rows = cur.execute(
                "SELECT id, title, text, bhavam, prathipadartham "
                "FROM poems WHERE search_text IS NULL LIMIT ?", (BATCH,)
            ).fetchall()
            if not rows:
                break
            updates = [
                (build_search_text(t, x, b, p), i) for (i, t, x, b, p) in rows
            ]
            cur.executemany("UPDATE poems SET search_text = ? WHERE id = ?", updates)
            con.commit()
            processed += len(rows)
            print(f"  {processed:>7,} / {total:,}  ({(time.perf_counter()-t0):.1f}s)")
        print(f"Backfill done in {time.perf_counter() - t0:.1f}s")

    # 3. Drop and re-create FTS table + triggers (idempotent).
    print("\nCreating FTS5 virtual table + sync triggers …")
    cur.executescript("""
        DROP TRIGGER IF EXISTS poems_fts_ai;
        DROP TRIGGER IF EXISTS poems_fts_ad;
        DROP TRIGGER IF EXISTS poems_fts_au;
        DROP TABLE  IF EXISTS poems_fts;

        CREATE VIRTUAL TABLE poems_fts USING fts5(
            search_text,
            content='poems',
            content_rowid='id',
            tokenize='trigram'
        );

        -- Keep FTS in sync on writes.
        CREATE TRIGGER poems_fts_ai AFTER INSERT ON poems BEGIN
            INSERT INTO poems_fts(rowid, search_text)
            VALUES (new.id, new.search_text);
        END;

        CREATE TRIGGER poems_fts_ad AFTER DELETE ON poems BEGIN
            INSERT INTO poems_fts(poems_fts, rowid, search_text)
            VALUES ('delete', old.id, old.search_text);
        END;

        CREATE TRIGGER poems_fts_au AFTER UPDATE ON poems BEGIN
            INSERT INTO poems_fts(poems_fts, rowid, search_text)
            VALUES ('delete', old.id, old.search_text);
            INSERT INTO poems_fts(rowid, search_text)
            VALUES (new.id, new.search_text);
        END;
    """)
    con.commit()

    # 4. Rebuild the FTS index from the content table.
    print("Building FTS index (rebuild) …")
    t0 = time.perf_counter()
    cur.execute("INSERT INTO poems_fts(poems_fts) VALUES('rebuild')")
    con.commit()
    print(f"  rebuild done in {time.perf_counter() - t0:.1f}s")

    # 5. Quick sanity check.
    n_fts = cur.execute("SELECT COUNT(*) FROM poems_fts").fetchone()[0]
    n_poems = cur.execute("SELECT COUNT(*) FROM poems").fetchone()[0]
    print(f"\npoems_fts rows : {n_fts:,}")
    print(f"poems rows     : {n_poems:,}")
    if n_fts != n_poems:
        print("WARN: counts differ; FTS may be out of sync.")
    con.close()


if __name__ == "__main__":
    main()
