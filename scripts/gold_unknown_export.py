#!/usr/bin/env python3
"""Gold (unknown-meter) — step 1 of 3: export the Unknown-meter poems to chunked
JSON for the headless chandassu scanner.

Complement to gold_scan_export.py (which exports *known*-meter poems to validate
them). Here we export the poems whose meter is Unknown so the scanner can find
the ones that actually scan 100% as a single meter — those then get reclassified
+ golded by gold_unknown_apply.py.

  ./venv/bin/python scripts/gold_unknown_export.py [out_dir]

Writes chunk_NNN.json of [{id, text}, ...] into out_dir (default
static/_goldscan_unknown/). out_dir is a scratch working dir — safe to delete
after the run; add it to .gitignore.
"""
import sqlite3
import json
import os
import shutil
import sys

DB = "padyarchana.db"
UNKNOWN = ("unknown", "Unknown", "UNKNOWN")
CHUNK = 5000


def main(out_dir):
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)

    con = sqlite3.connect(DB)
    ph = ",".join("?" * len(UNKNOWN))
    mids = [r[0] for r in con.execute(
        f"SELECT id FROM meters WHERE name IN ({ph})", UNKNOWN).fetchall()]
    if not mids:
        print("no Unknown meter row found")
        return
    mph = ",".join("?" * len(mids))
    rows = con.execute(
        f"""SELECT id, text FROM poems
            WHERE meter_id IN ({mph}) AND text IS NOT NULL AND text != ''
            ORDER BY id""", mids).fetchall()
    con.close()

    n = 0
    for i in range(0, len(rows), CHUNK):
        part = [{"id": r[0], "text": r[1]} for r in rows[i:i + CHUNK]]
        with open(f"{out_dir}/chunk_{n:03d}.json", "w", encoding="utf-8") as f:
            json.dump(part, f, ensure_ascii=False)
        n += 1

    print(f"exported {len(rows)} Unknown-meter poems into {n} chunks -> {out_dir}")
    print("next: node scripts/chandam_headless_scan.mjs", out_dir)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "static/_goldscan_unknown"
    main(out)
