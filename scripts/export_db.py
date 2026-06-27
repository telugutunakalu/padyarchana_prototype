#!/usr/bin/env python3
"""Export the full padyarchana DB to round-trippable JSON under db_export/.

This captures everything the crawled padyalu_json_data/ JSONs do NOT — admin
ratings, bhavam, prathipadartham, in-app poem edits, and full poet/meter
metadata (era, copyright flag, bios). db_export/ — not the crawled corpus — is
the canonical, reimportable snapshot of DB state. Pair with import_db.py.

Layout:
  db_export/poets.json          all poets, full metadata (id-keyed)
  db_export/meters.json         all meters, full metadata (id-keyed)
  db_export/poems/<slug>.json   poems grouped by source (one file per source)
  db_export/manifest.json       counts + source→file map (integrity reference)

Derived columns (word_count/gana_count/line_count/search_text) are intentionally
omitted — import_db.py recomputes them deterministically. ids are preserved so
the round-trip is exact. Read-only: never writes to the DB.
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "padyarchana.db"
OUT = ROOT / "db_export"

# --- compact deterministic Telugu→ASCII slug (filenames only) ---------------
_V = {"అ": "a", "ఆ": "aa", "ఇ": "i", "ఈ": "ii", "ఉ": "u", "ఊ": "uu", "ఋ": "ru",
      "ఎ": "e", "ఏ": "e", "ఐ": "ai", "ఒ": "o", "ఓ": "o", "ఔ": "au"}
_M = {"ా": "aa", "ి": "i", "ీ": "ii", "ు": "u", "ూ": "uu", "ృ": "ru", "ె": "e",
      "ే": "e", "ై": "ai", "ొ": "o", "ో": "o", "ౌ": "au"}
_C = {"క": "k", "ఖ": "kh", "గ": "g", "ఘ": "gh", "ఙ": "n", "చ": "ch", "ఛ": "chh",
      "జ": "j", "ఝ": "jh", "ఞ": "n", "ట": "t", "ఠ": "th", "డ": "d", "ఢ": "dh",
      "ణ": "n", "త": "t", "థ": "th", "ద": "d", "ధ": "dh", "న": "n", "ప": "p",
      "ఫ": "ph", "బ": "b", "భ": "bh", "మ": "m", "య": "y", "ర": "r", "ల": "l",
      "వ": "v", "శ": "sh", "ష": "sh", "స": "s", "హ": "h", "ళ": "l", "ఱ": "r"}
_VIR = "్"


def romanize(s: str) -> str:
    out, i = [], 0
    while i < len(s):
        ch = s[i]
        if ch in _C:
            out.append(_C[ch])
            if i + 1 < len(s) and s[i + 1] == _VIR:
                i += 2; continue
            if i + 1 < len(s) and s[i + 1] in _M:
                out.append(_M[s[i + 1]]); i += 2; continue
            out.append("a"); i += 1; continue
        if ch in _V:
            out.append(_V[ch]); i += 1; continue
        if ch == "ం":
            out.append("m")
        i += 1
    return re.sub(r"[^a-z0-9]+", "_", "".join(out).lower()).strip("_")


def _jload(v):
    if isinstance(v, str) and v:
        try:
            return json.loads(v)
        except Exception:
            return v
    return v


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    (OUT / "poems").mkdir(parents=True, exist_ok=True)

    poets = [dict(r) for r in con.execute(
        "SELECT id,name,name_english,biography,era,birth_year,death_year,"
        "copyright_protected FROM poets ORDER BY id")]
    (OUT / "poets.json").write_text(json.dumps(poets, ensure_ascii=False, indent=1), encoding="utf-8")

    meters = []
    for r in con.execute("SELECT id,name,name_english,description,gana_structure,"
                         "example_pattern FROM meters ORDER BY id"):
        m = dict(r); m["gana_structure"] = _jload(m["gana_structure"]); meters.append(m)
    (OUT / "meters.json").write_text(json.dumps(meters, ensure_ascii=False, indent=1), encoding="utf-8")

    # poem edit-history (app correction trail: title/text/meter/rating/bhavam per version)
    versions = []
    for r in con.execute(
        "SELECT id,poem_id,version_no,title,text,literary_form,meter_id,rating,"
        "prathipadartham,bhavam,created_by,created_at FROM poem_versions ORDER BY id"):
        v = dict(r); v["prathipadartham"] = _jload(v["prathipadartham"]); versions.append(v)
    (OUT / "poem_versions.json").write_text(json.dumps(versions, ensure_ascii=False, indent=1), encoding="utf-8")

    sources = [r[0] for r in con.execute(
        "SELECT DISTINCT source FROM poems ORDER BY source")]
    slugs, used = {}, set()
    for s in sources:
        base = (romanize(s or "") or "source")[:60]
        slug, k = base, 2
        while slug in used:
            slug = f"{base}_{k}"; k += 1
        used.add(slug); slugs[s] = slug

    manifest = {"poets_total": len(poets), "meters_total": len(meters),
                "poems_total": 0, "sources_total": len(sources), "sources": []}
    # clear stale per-source files
    for old in (OUT / "poems").glob("*.json"):
        old.unlink()
    for s in sources:
        rows = con.execute(
            "SELECT p.id,p.title,p.text,p.literary_form,p.source,p.kanda,p.flags,"
            "p.rating,p.prathipadartham,p.bhavam,p.word_count,p.gana_count,p.line_count,"
            "p.poet_id,po.name AS poet_name,"
            "p.meter_id,m.name AS meter_name "
            "FROM poems p LEFT JOIN poets po ON p.poet_id=po.id "
            "LEFT JOIN meters m ON p.meter_id=m.id "
            "WHERE p.source IS ? ORDER BY p.id", (s,)).fetchall()
        poems = []
        for r in rows:
            d = dict(r); d["prathipadartham"] = _jload(d["prathipadartham"]); poems.append(d)
        slug = slugs[s]
        (OUT / "poems" / f"{slug}.json").write_text(
            json.dumps({"source": s, "count": len(poems), "poems": poems},
                       ensure_ascii=False, indent=1), encoding="utf-8")
        manifest["poems_total"] += len(poems)
        manifest["sources"].append({"source": s, "file": f"poems/{slug}.json", "count": len(poems)})

    manifest["poem_versions_total"] = len(versions)
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    rated = con.execute("SELECT count(*) FROM poems WHERE rating IS NOT NULL").fetchone()[0]
    bhav = con.execute("SELECT count(*) FROM poems WHERE bhavam IS NOT NULL").fetchone()[0]
    print(f"exported {manifest['poems_total']} poems / {len(poets)} poets / {len(meters)} meters "
          f"across {len(sources)} source files")
    print(f"  carried DB-only corrections: {rated} ratings, {bhav} bhavam, "
          f"{len(versions)} poem-version history rows → db_export/")


if __name__ == "__main__":
    main()
