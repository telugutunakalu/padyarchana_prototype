#!/usr/bin/env python3
"""Rebuild a padyarchana DB from a db_export/ snapshot (the inverse of
export_db.py). Full-fidelity and id-preserving: restores poets, meters and
poems including ratings / bhavam / prathipadartham / in-app edits, recomputes
the derived columns (word_count, line_count, search_text) exactly as the import
pipeline does, and rebuilds the FTS5 trigram index.

Usage:
  python scripts/import_db.py                       # rebuild ./padyarchana.db
  python scripts/import_db.py --db /tmp/test.db     # rebuild a different DB (round-trip test)
  python scripts/import_db.py --export-dir db_export --reset

--reset wipes poems/poets/meters first (clean rebuild). Without it, the script
refuses to run if those tables are non-empty (avoids silent double-import).
MUST run under ./venv/bin/python — the venv sqlite3 has FTS5; the system one
does not and would silently break the poems_fts triggers.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sqlalchemy import create_engine  # noqa: E402
from app.database import Base  # noqa: E402
import app.models  # noqa: E402,F401  (registers all tables on Base.metadata)
from app.utils.search_text import build_search_text  # noqa: E402

FTS_DDL = """
DROP TRIGGER IF EXISTS poems_fts_ai;
DROP TRIGGER IF EXISTS poems_fts_ad;
DROP TRIGGER IF EXISTS poems_fts_au;
DROP TABLE  IF EXISTS poems_fts;
CREATE VIRTUAL TABLE poems_fts USING fts5(
    search_text, content='poems', content_rowid='id', tokenize='trigram');
CREATE TRIGGER poems_fts_ai AFTER INSERT ON poems BEGIN
    INSERT INTO poems_fts(rowid, search_text) VALUES (new.id, new.search_text);
END;
CREATE TRIGGER poems_fts_ad AFTER DELETE ON poems BEGIN
    INSERT INTO poems_fts(poems_fts, rowid, search_text) VALUES ('delete', old.id, old.search_text);
END;
CREATE TRIGGER poems_fts_au AFTER UPDATE ON poems BEGIN
    INSERT INTO poems_fts(poems_fts, rowid, search_text) VALUES ('delete', old.id, old.search_text);
    INSERT INTO poems_fts(rowid, search_text) VALUES (new.id, new.search_text);
END;
"""


def _dump(v):
    return json.dumps(v, ensure_ascii=False) if v is not None and not isinstance(v, str) else v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export-dir", default=str(ROOT / "db_export"))
    ap.add_argument("--db", default=str(ROOT / "padyarchana.db"))
    ap.add_argument("--reset", action="store_true", help="wipe poems/poets/meters first")
    args = ap.parse_args()
    EXP = Path(args.export_dir)

    # 1. schema (creates every model table EXCEPT the FTS virtual table)
    eng = create_engine(f"sqlite:///{args.db}")
    Base.metadata.create_all(eng)
    eng.dispose()

    con = sqlite3.connect(args.db)
    cur = con.cursor()
    n_existing = cur.execute("SELECT count(*) FROM poems").fetchone()[0]
    if n_existing and not args.reset:
        sys.exit(f"refusing: {args.db} already has {n_existing} poems; pass --reset to rebuild")
    if args.reset:
        for t in ("poems", "poets", "meters"):
            cur.execute(f"DELETE FROM {t}")

    # 2. poets
    poets = json.loads((EXP / "poets.json").read_text())
    cur.executemany(
        "INSERT INTO poets(id,name,name_english,biography,era,birth_year,death_year,"
        "copyright_protected) VALUES(?,?,?,?,?,?,?,?)",
        [(p["id"], p["name"], p.get("name_english"), p.get("biography"), p.get("era"),
          p.get("birth_year"), p.get("death_year"), p.get("copyright_protected", 1)) for p in poets])

    # 3. meters
    meters = json.loads((EXP / "meters.json").read_text())
    cur.executemany(
        "INSERT INTO meters(id,name,name_english,description,gana_structure,example_pattern) "
        "VALUES(?,?,?,?,?,?)",
        [(m["id"], m["name"], m.get("name_english"), m.get("description"),
          _dump(m.get("gana_structure")), m.get("example_pattern")) for m in meters])

    # 4. poems (derived columns recomputed; ids preserved)
    rows, n = [], 0
    for f in sorted((EXP / "poems").glob("*.json")):
        for p in json.loads(f.read_text())["poems"]:
            text = p["text"]
            prathi, bhavam, title = p.get("prathipadartham"), p.get("bhavam"), (p.get("title") or "")
            st = build_search_text(title[:500], text, bhavam, prathi)
            # derived counts are preserved from the snapshot (historical values
            # came from heterogeneous import paths; recomputing would drift)
            rows.append((p["id"], title[:500], text, p.get("literary_form"),
                         p.get("word_count"), p.get("gana_count"), p.get("line_count"),
                         p.get("source"), p.get("kanda"), _dump(prathi), bhavam,
                         p.get("flags"), p.get("rating"), st, p.get("poet_id"), p.get("meter_id")))
            n += 1
            if len(rows) >= 5000:
                _flush(cur, rows); con.commit(); rows = []
    if rows:
        _flush(cur, rows)
    con.commit()

    # 5. FTS5 rebuild
    cur.executescript(FTS_DDL)
    cur.execute("INSERT INTO poems_fts(poems_fts) VALUES('rebuild')")
    con.commit()

    n_poems = cur.execute("SELECT count(*) FROM poems").fetchone()[0]
    n_fts = cur.execute("SELECT count(*) FROM poems_fts").fetchone()[0]
    n_poets = cur.execute("SELECT count(*) FROM poets").fetchone()[0]
    cur.execute("INSERT INTO poems_fts(poems_fts) VALUES('integrity-check')")
    con.commit()
    con.close()
    print(f"rebuilt {args.db}: {n_poems} poems / {n_poets} poets / {len(meters)} meters")
    print(f"  FTS5 rows: {n_fts} (== poems: {n_fts == n_poems}) | integrity-check: PASS")


def _flush(cur, rows):
    cur.executemany(
        "INSERT INTO poems(id,title,text,literary_form,word_count,gana_count,line_count,"
        "source,kanda,prathipadartham,bhavam,flags,rating,search_text,poet_id,meter_id) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)


if __name__ == "__main__":
    main()
