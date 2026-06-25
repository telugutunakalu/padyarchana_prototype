#!/usr/bin/env python3
"""Structure పాంచాలీపరిణయము (కాకమాని మూర్తి, 1894) from Wikisource.

This is a *proofread* page (clean line breaks, standard meter markers, no per-verse
numbers), so we reuse the general clean-text padya parser from text_to_json
(marker split, సీసము+గీత merge, prose/header skip) across the 5 ఆశ్వాసములు — no
salvage heuristics needed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wikisource_crawler as w  # noqa: E402
import text_to_json as t  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "padyalu_json_data"
WORK = "పాంచాలీపరిణయము"
CHAPTERS = ["ప్రథమాశ్వాసము", "ద్వితీయాశ్వాసము", "తృతీయాశ్వాసము",
            "చతుర్థాశ్వాసము", "పంచమాశ్వాసము"]


def main() -> None:
    all_poems: list[dict] = []
    for ch in CHAPTERS:
        txt = w.fetch_rendered(f"{WORK}/{ch}")
        ps = t.parse_padyalu(txt, fixed_chapter=ch)
        print(f"  {ch}: {len(ps)} padyalu")
        all_poems.extend(ps)
    all_poems = [{"id": i, **p} for i, p in enumerate(all_poems, 1)]
    rec = {
        "shatakam_title_telugu": WORK,
        "author_telugu": "కాకమాని మూర్తి",
        "year": 1894,
        "literary_form_telugu": "ప్రబంధము",
        "source_url": "https://te.wikisource.org/wiki/" + WORK,
        "poems": all_poems,
    }
    OUT.mkdir(exist_ok=True)
    fp = OUT / "panchaliparinayamu_kakamani_murti.json"
    fp.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n-> {fp.name} ({len(all_poems)} padyalu)")


if __name__ == "__main__":
    main()
