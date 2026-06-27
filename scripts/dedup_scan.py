#!/usr/bin/env python3
"""Corpus-wide duplicate-WORK scan — find pairs of sources that are the same work
onboarded twice under different source/poet name spellings (the శివశతకము /
ప్రబంధసారశిరోమణి pattern).

Builds a normalized verse → sources map, then reports source pairs whose mutual
verse overlap is high (>= --ratio of the smaller source's verses). A near-100%
pair is almost certainly a duplicated work; a 50–90% pair is usually a work that
also appears inside an anthology (legitimate — review). Read-only.

Usage:
  ./venv/bin/python scripts/dedup_scan.py [--ratio 0.5] [--min-shared 5]
"""
from __future__ import annotations

import argparse
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "padyarchana.db"
_TEL = re.compile(r"[^ఀ-౿]")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ratio", type=float, default=0.5, help="min shared/smaller-source ratio")
    ap.add_argument("--min-shared", type=int, default=5)
    ap.add_argument("--max-spread", type=int, default=8,
                    help="ignore verses shared across more than this many sources (ubiquitous quotes)")
    args = ap.parse_args()

    con = sqlite3.connect(DB)
    src_verses: dict[str, set] = defaultdict(set)
    verse_srcs: dict[str, set] = defaultdict(set)
    for src, text in con.execute("SELECT source, text FROM poems"):
        nt = _TEL.sub("", text or "")
        if len(nt) < 24:
            continue
        src_verses[src].add(nt)
        verse_srcs[nt].add(src)

    pair: dict[tuple, int] = defaultdict(int)
    for srcs in verse_srcs.values():
        if 2 <= len(srcs) <= args.max_spread:
            s = sorted(srcs)
            for i in range(len(s)):
                for j in range(i + 1, len(s)):
                    pair[(s[i], s[j])] += 1

    rows = []
    for (a, b), sh in pair.items():
        m = min(len(src_verses[a]), len(src_verses[b]))
        r = sh / m if m else 0
        if r >= args.ratio and sh >= args.min_shared:
            rows.append((r, sh, len(src_verses[a]), len(src_verses[b]), a, b))
    rows.sort(reverse=True)

    print(f"{len(src_verses)} sources scanned; candidate duplicate-work pairs "
          f"(>= {args.ratio:.0%} of smaller shared): {len(rows)}\n")
    for r, sh, na, nb, a, b in rows:
        tag = "IDENTICAL" if r >= 0.99 else "high-overlap"
        print(f"  [{tag:12s}] {r:3.0%} shared={sh:4d} | {a} ({na})  ~  {b} ({nb})")
    if not rows:
        print("  (none — corpus is clean at the work level)")


if __name__ == "__main__":
    main()
