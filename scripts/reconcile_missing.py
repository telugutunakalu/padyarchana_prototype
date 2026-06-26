#!/usr/bin/env python3
"""Reconcile the ~442 poems present in padyalu_json_data/*.json but absent from
the live DB. Aligns authors/sources to existing DB attribution (no poet-splits),
strips stray {{…}} markup, and onboards with the per-poem duplicate check ON so
ONLY the genuinely-missing poems are added (existing rows are skipped, never
duplicated). Run via ./venv/bin/python."""
import asyncio
import json
import logging
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from app.database import AsyncSessionLocal, engine  # noqa: E402
from scripts.import_json import import_poems_from_json, ensure_tables_exist  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
JD = ROOT / "padyalu_json_data"

# author/source corrections so missing poems join the existing DB attribution
FIX = {
    "vemana_201_299": {"author_telugu": "వేమన", "shatakam_title_telugu": "వేమన శతకము"},
    "andhra_nayaka_satakam": {"author_telugu": "కాసుల పురుషోత్తమకవి"},
    "narayana_satakam": {"author_telugu": "Unknown"},
    "sampangimanna_satakam": {"author_telugu": "Unknown"},
}
FILES = ["vemana_201_299", "vemana_301_467", "abhagyopakhyanamu_kandukuri_veereshalingam",
         "narayana_satakam", "sampangimanna_satakam", "agha_vinasha_satakam",
         "srinivasa_vilasa_sevadhi", "chandodarpanamu_anantamatya",
         "achchatelugu_ramayanamu_kuchimanchi_timmakavi", "andhra_nayaka_satakam"]

_MK = re.compile(r"\{\{[^}]*\}?\}?|\}\}")


def clean_markup(d: dict) -> int:
    """Strip {{…}} template lines from poems that carry them (only the missing
    poems do; existing rows are markup-free, so this never alters imported text)."""
    changed = 0
    for p in d.get("poems", []):
        lines = p.get("lines_telugu", [])
        if not any("{{" in ln or "}}" in ln for ln in lines):
            continue
        new = []
        for ln in lines:
            if "{{" in ln or "}}" in ln:
                ln = _MK.sub(" ", ln).replace("{", "").replace("}", "")
                ln = re.sub(r"\s+", " ", ln).strip()
                if len(ln) < 6:        # was a pure heading line → drop
                    continue
            new.append(ln)
        p["lines_telugu"] = new
        changed += 1
    return changed


async def main():
    # 1. fix JSON metadata + markup, save
    for fn in FILES:
        fp = JD / f"{fn}.json"
        d = json.loads(fp.read_text())
        for k, v in FIX.get(fn, {}).items():
            d[k] = v
        mk = clean_markup(d)
        fp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        if fn in FIX or mk:
            print(f"  fixed {fn}: {FIX.get(fn, {})}{' +markup' if mk else ''}", flush=True)

    # 2. onboard with duplicate check ON → only missing rows added
    await ensure_tables_exist()
    total = 0
    async with AsyncSessionLocal() as db:
        for fn in FILES:
            r = await import_poems_from_json(db, str(JD / f"{fn}.json"),
                                             skip_duplicate_check=False, batch_size=500)
            total += r["imported"]
            print(f"  [{fn[:40]:40s}] +{r['imported']:4d} new  ({r['skipped']} already present)", flush=True)
    await engine.dispose()
    print(f"\n=== RECONCILE COMPLETE: {total} missing poems added ===")


if __name__ == "__main__":
    asyncio.run(main())
