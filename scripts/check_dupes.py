#!/usr/bin/env python3
"""Pre-onboard duplicate gate — verse-level (padyam) dedup check.

Compares a to-be-onboarded JSON's verses against every verse already in the DB
by NORMALIZED TEXT (Telugu code points only), independent of source-name or
poet-name spelling. This catches the variant-name duplicates that exact
source/poet matching misses (e.g. శివశతకము vs "శివ శతకం", or two editions of one
anthology). Run this BEFORE onboarding any new JSON.

Usage:
  ./venv/bin/python scripts/check_dupes.py path/to/file.json [more.json ...]
  ./venv/bin/python scripts/check_dupes.py crawlers/wikibook3_json/   # a directory

Verdict per file: DUPLICATE (>=60% of its verses already in DB), partial-overlap
(>=15%), or new. For overlaps it names the existing source(s) the verses match,
so you can decide skip / merge-missing / replace. Read-only; never writes.
"""
from __future__ import annotations

import glob
import json
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "padyarchana.db"
_TEL = re.compile(r"[^ఀ-౿]")


def norm(t) -> str:
    if isinstance(t, list):
        t = "".join(t)
    return _TEL.sub("", t or "")


def load_db_verses() -> dict:
    con = sqlite3.connect(DB)
    m: dict[str, str] = {}
    for src, text in con.execute("SELECT source, text FROM poems"):
        k = norm(text)
        if len(k) >= 10:
            m.setdefault(k, src)
    return m


def check(path: str, dbmap: dict):
    d = json.loads(Path(path).read_text())
    poems = d.get("poems", [])
    hits: Counter = Counter()
    matched = 0
    for p in poems:
        nt = norm(p.get("lines_telugu") or p.get("text") or "")
        if len(nt) < 10:
            continue
        src = dbmap.get(nt)
        if src is not None:
            matched += 1
            hits[src] += 1
    return len(poems), matched, hits


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit("usage: check_dupes.py <file.json | dir> [...]")
    files: list[str] = []
    for a in args:
        files += sorted(glob.glob(f"{a}/*.json")) if Path(a).is_dir() else [a]
    dbmap = load_db_verses()
    print(f"DB: {len(dbmap)} distinct verse texts\n")
    any_dup = False
    for f in files:
        try:
            n, matched, hits = check(f, dbmap)
        except Exception as e:
            print(f"  {Path(f).name}: ERROR {e}")
            continue
        pct = 100 * matched // max(1, n)
        verdict = "DUPLICATE" if pct >= 60 else ("partial-overlap" if pct >= 15 else "new")
        if pct >= 15:
            any_dup = True
        print(f"[{verdict:15s}] {Path(f).name}: {matched}/{n} verses ({pct}%) already in DB")
        for src, cnt in hits.most_common(3):
            print(f"        {cnt:5d} match → {src}")
    if any_dup:
        print("\n⚠  overlaps found — review before onboarding (skip / merge-missing-verses / replace).")


if __name__ == "__main__":
    main()
