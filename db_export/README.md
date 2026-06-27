# db_export — canonical DB snapshot (import/export protocol)

This folder is the **full-fidelity, round-trippable JSON snapshot of `padyarchana.db`**.
Unlike `padyalu_json_data/` (raw crawl output — verse text only), this captures
everything that is **DB-only** and would otherwise be lost on a rebuild:

- **bhavam** (verse meaning summaries) — ~117k poems
- **prathipadartham** (word-by-word glosses)
- admin **rating** (gold/silver/bronze)
- in-app **poem edits** (title / text / meter)
- full **poet** metadata — era (incl. corrections), copyright flag, bios
- full **meter** metadata

## Layout
```
db_export/
  poets.json            all poets, full metadata (id-keyed)
  meters.json           all meters, full metadata (id-keyed)
  poems/<slug>.json     poems grouped by source (one file per source)
  manifest.json         counts + source→file map (integrity reference)
```
ids are preserved, so the round-trip is exact.

## Protocol

**Export** (DB → JSON, after making corrections in the app):
```
./venv/bin/python scripts/export_db.py
```

**Import / rebuild** (JSON → DB):
```
./venv/bin/python scripts/import_db.py --reset           # rebuild ./padyarchana.db
./venv/bin/python scripts/import_db.py --db /tmp/x.db    # into a different DB
```
Restores poets, meters and poems including all corrections, recomputes the FTS5
trigram index, and runs an integrity check. **Always use `./venv/bin/python`** —
the system `sqlite3` lacks FTS5 and would silently break the `poems_fts` triggers.

## Workflow
1. Make corrections via the app (ratings, edits, bhavam, …).
2. `export_db.py` → updates this folder.
3. Commit the diff (small, per-source files keep diffs readable).
4. Anyone can `import_db.py --reset` to rebuild the exact DB from git.

This snapshot — not `padyalu_json_data/` — is the source of truth for DB state.
