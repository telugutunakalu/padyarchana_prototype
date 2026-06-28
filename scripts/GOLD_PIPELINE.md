# Chandassu gold auto-tagging pipeline

Metrically scan poems with the real **Chandam** engine (the same
`static/chandam/chandam.te.app.min.js` the website uses) and, for verses that
scan a **perfect 100%** to a single meter, set the meter + tag them `gold`.

The scanner runs the browser engine **headlessly** via jsdom under Node — no
browser, no Chromium. Yati uses **`experimentalSandhi=true`**
(*అచ్చు ఆధారంగా సంధియుత యతి మైత్రి గుర్తింపు*, vowel-based sandhi yati-maitri),
plus the normal yati + prasa checks. See `chandam_headless_scan.mjs` `OPTS`.

One-time setup:

```bash
npm --prefix scripts install        # installs jsdom (~16 MB; node_modules is gitignored)
```

## A. Reclassify + gold the Unknown-meter poems

```bash
# 1. export the Unknown-meter poems to chunks
./venv/bin/python scripts/gold_unknown_export.py            # -> static/_goldscan_unknown/

# 2. scan them headlessly; writes pairs_*.json of [id, meter] for 100% matches
node scripts/chandam_headless_scan.mjs static/_goldscan_unknown

# 3. apply: map detected meter -> DB meter row, set meter_id + rating='gold'
#    (only currently-unrated poems are golded). Writes scripts/gold_unknown_undo.json
./venv/bin/python scripts/gold_unknown_apply.py static/_goldscan_unknown/pairs --dry   # preview
./venv/bin/python scripts/gold_unknown_apply.py static/_goldscan_unknown/pairs         # apply
```

`gold_unknown_apply.py` only maps a detected meter to an **existing** DB meter
(skips fragments like `సీసం2-పూర్వభాగము` and rare vṛttas not in the DB — it
reports the unmapped tally). To onboard genuinely-new rare meters the scan finds,
create the meter row first, then assign those poem-ids.

Undo: `./venv/bin/python scripts/gold_unknown_undo.py` (restores meter_id +
clears the gold this run set).

Clean up the scratch dir when done: `rm -rf static/_goldscan_unknown`.

## B. Validate (and gold) the already-known-meter poems

```bash
./venv/bin/python scripts/gold_scan_export.py              # -> static/_goldscan/ (known meters)
node scripts/chandam_headless_scan.mjs static/_goldscan
# then a per-poem confirm/gold step against static/_goldscan/pairs
```

Undo for that path: ids in `scripts/gold_autotagged_ids.json`, via
`scripts/gold_scan_undo.py`.

## Notes
- The scanner is **resumable** — a chunk whose `pairs_*.json` already exists is
  skipped. ~4 ms/poem (≈3 min for 35 K poems).
- All DB writes go through `./venv/bin/python` (the system sqlite3 CLI lacks FTS5
  and would break the `poems_fts` triggers).
- These are DB-only changes — run `scripts/export_db.py` afterwards to capture
  the new ratings/meters in `db_export/`.
