#!/usr/bin/env python3
"""Structure సర్పపురమాహాత్మ్యము (కూచిమంచి తిమ్మన, 1896) from Wikisource.

A proofread, verse-numbered work. The general clean-text parser handles the body,
but each ఆశ్వాసము opens with an *unmarked* invocatory padyam (no meter abbrev) that
the parser skips. By convention that first padyam begins with the శ్రీకారం; in the
scan the శ్రీ drop-cap is dropped for the కంద ones (ద్వితీయ/తృతీయ). So we capture the
first padyam explicitly, prepend శ్రీ when missing, and label its meter, then let
text_to_json.parse_padyalu handle the rest.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wikisource_crawler as w  # noqa: E402
import text_to_json as t  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "padyalu_json_data"
WORK = "సర్పపురమాహాత్మ్యము"
CHAPTERS = ["పీఠిక", "ప్రథమాశ్వాసము", "ద్వితీయాశ్వాసము", "తృతీయాశ్వాసము"]
# meter of each ఆశ్వాసము's opening (unmarked) padyam — verified by gana/structure
FIRST_METER = {"ప్రథమాశ్వాసము": "ఉత్పలమాల", "ద్వితీయాశ్వాసము": "కందము", "తృతీయాశ్వాసము": "కందము"}

_NUMLINE = re.compile(r"^[0-9౦-౯]+$")


def first_padyam(text: str, chapter: str) -> list[str] | None:
    """The opening unmarked padyam = lines after the ఆశ్వాసము title up to its
    verse number '1'. Prepend the శ్రీకారం if the drop-cap was lost."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if chapter not in lines:
        return None
    out: list[str] = []
    for ln in lines[lines.index(chapter) + 1:]:
        if _NUMLINE.match(ln) or t._marker(ln):  # number or a marked verse ends it
            break
        out.append(ln)
    if len(out) < 2:
        return None
    if not out[0].startswith("శ్రీ"):
        out[0] = "శ్రీ" + out[0]
    return out


def main() -> None:
    all_poems: list[dict] = []
    for ch in CHAPTERS:
        txt = w.fetch_rendered(f"{WORK}/{ch}")
        ch_poems: list[dict] = []
        if ch in FIRST_METER:
            fp = first_padyam(txt, ch)
            if fp:
                ch_poems.append({
                    "lines_telugu": fp, "Chandassu": FIRST_METER[ch],
                    "chapter": ch, "padyam_number": 1,
                    "bhavam": None, "prathipadartham": None,
                })
        ch_poems.extend(t.parse_padyalu(txt, fixed_chapter=ch))
        print(f"  {ch}: {len(ch_poems)} padyalu")
        all_poems.extend(ch_poems)
    all_poems = [{"id": i, **p} for i, p in enumerate(all_poems, 1)]
    rec = {
        "shatakam_title_telugu": WORK,
        "author_telugu": "కూచిమంచి తిమ్మన",
        "year": 1896,
        "literary_form_telugu": "ప్రబంధము",
        "source_url": "https://te.wikisource.org/wiki/" + WORK,
        "poems": all_poems,
    }
    OUT.mkdir(exist_ok=True)
    fp_out = OUT / "sarpapuramahatmyamu_kuchimanchi_timmana.json"
    fp_out.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n-> {fp_out.name} ({len(all_poems)} padyalu)")


if __name__ == "__main__":
    main()
