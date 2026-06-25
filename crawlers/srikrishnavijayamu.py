#!/usr/bin/env python3
"""Salvage clear Telugu padyalu from శ్రీకృష్ణవిజయము (పూసపాటి తమ్మభూపాలుడు, 1893).

Like ఉత్తరహరిశ్చంద్రోపాఖ్యానము, this Wikisource text is an UNPROOFREAD OCR of an
1893 print: each ఆశ్వాసము renders as one long garbled paragraph with verses run
together, but the meter markers (శా॥ సీ॥ చ॥ ఉ॥ మ॥ క॥ …) and trailing verse numbers
survive. We split on those markers, segment each span into padams on the inline
dandas (| ! ।), strip running-header/spine noise, and keep only discernible verses
(meter-fitting padam count, a real verse number, almost-entirely-Telugu lines).

The verse *text* stays OCR-imperfect (inherent to the source); meter + padam count
+ number + ఆశ్వాసము are what is reliably recoverable.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wikisource_crawler as w  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "padyalu_json_data"
WORK = "శ్రీకృష్ణవిజయము"
CHAPTERS = ["ఉపోద్ఘాతము", "ప్రథమాశ్వాసము", "ద్వితీయాశ్వాసము",
            "తృతీయాశ్వాసము", "చతుర్థాశ్వాసము", "పంచమాశ్వాసము"]

METER = {
    "శా": "శార్దూలవిక్రీడితము", "సీ": "సీసము", "మత్త": "మత్తకోకిల",
    "తే": "తేటగీతి", "గీ": "గీతము", "మాలి": "మాలిని", "స్రగ్ధ": "స్రగ్ధర",
    "చ": "చంపకమాల", "ఉ": "ఉత్పలమాల", "మ": "మత్తేభవిక్రీడితము",
    "క": "కందము", "ఆ": "ఆటవెలది", "వ": "వచనము",
}
_ALT = "|".join(sorted(METER, key=len, reverse=True))
MARK = re.compile(rf"(?<![ఀ-౿])({_ALT})\s*(?:॥|\|\|?)")
PADAM = re.compile(r"[|!।॥]+")
NUM = re.compile(r"[0-9౦-౯]+")
# repeated running-header / opening-invocation spine to delete before splitting
HEADER = re.compile(
    r"శ్రీకృష్ణవిజయము[.\s]*|శ్రీ\s*కృష్ణవిజయము[.\s]*"
    r"|శుభమస్తు[^.]{0,40}?నమః|శివాభ్యాంనమః|శ్రీగురుభ్యోనమ\S*"
)
# running-header / section-label tokens that leak into verse lines
_LEAK = re.compile(
    r"కథాప్రారంభము|కథారంభము|ఉపోద్ఘాతము|శ్రీకృష్ణవిజయము|కృష్ణవిజయము"
    r"|ప్రథమాశ్వాసము|ద్వితీయాశ్వాసము|తృతీయాశ్వాసము|చతుర్థాశ్వాసము|పంచమాశ్వాసము"
    r"|[A-Za-z]+|[+*]\d*"
)
_TEL = re.compile(r"[ఀ-౿]")

# 4-padam vruttas must give EXACTLY 4 clean lines; సీసము a wider range; వచనము is
# dropped (unreliable in this OCR).
PADAM_RANGE = {"సీసము": (6, 9)}  # narrower: 10+ lines are merged runaways
_DEFAULT_RANGE = (4, 4)
_DROP_METERS = {"వచనము"}


def _clean_line(s: str) -> str:
    s = _LEAK.sub(" ", s)
    s = re.sub(r"[^ఀ-౿\s]", " ", s)  # keep only Telugu + space (drop brackets/latin/digits/symbols)
    return re.sub(r"\s+", " ", s).strip()


def _telugu_ratio(s: str) -> float:
    nonspace = [c for c in s if not c.isspace()]
    return len(_TEL.findall(s)) / len(nonspace) if nonspace else 0.0


def parse_chapter(text: str, chapter: str) -> list[dict]:
    text = HEADER.sub(" ", text)
    ms = list(MARK.finditer(text))
    poems: list[dict] = []
    for i, m in enumerate(ms):
        start = m.end()
        end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        block = text[start:end]
        nums = NUM.findall(block)
        number = int(nums[-1]) if nums and nums[-1].isdigit() else "unknown"
        if number == 0:           # a 0 is a spurious page artifact, not a verse number
            number = "unknown"
        body = re.sub(r"[॥|।\s]*[0-9౦-౯]+[.\s]*$", "", block)
        lines = [_clean_line(p) for p in PADAM.split(body)]
        lines = [ln for ln in lines if len(ln) >= 6 and _telugu_ratio(ln) >= 0.85]
        chandassu = METER[m.group(1)]
        if number == "unknown" or chandassu in _DROP_METERS:
            continue
        lo, hi = PADAM_RANGE.get(chandassu, _DEFAULT_RANGE)
        if not (lo <= len(lines) <= hi):
            continue
        if sum(len(ln) for ln in lines) < 50:
            continue
        if max(len(ln) for ln in lines) > 3 * (sum(len(ln) for ln in lines) / len(lines)):
            continue
        poems.append({
            "lines_telugu": lines,
            "Chandassu": chandassu,
            "chapter": chapter,
            "padyam_number": number,
            "bhavam": None,
            "prathipadartham": None,
        })
    return poems


def main() -> None:
    all_poems: list[dict] = []
    for ch in CHAPTERS:
        txt = w.fetch_rendered(f"{WORK}/{ch}")
        ps = parse_chapter(txt, ch)
        print(f"  {ch}: {len(ps)} salvaged padyalu")
        all_poems.extend(ps)
    all_poems = [{"id": i, **p} for i, p in enumerate(all_poems, 1)]
    rec = {
        "shatakam_title_telugu": WORK,
        "author_telugu": "పూసపాటి తమ్మభూపాలుడు",
        "year": 1893,
        "literary_form_telugu": "ప్రబంధము",
        "source_url": "https://te.wikisource.org/wiki/" + WORK,
        "flag": "OCR-sourced",
        "note": "Salvaged from an unproofread OCR; verse text is OCR-garbled.",
        "poems": all_poems,
    }
    OUT.mkdir(exist_ok=True)
    fp = OUT / "srikrishnavijayamu_pusapati_tammabhupaludu.json"
    fp.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n-> {fp.name} ({len(all_poems)} padyalu)")


if __name__ == "__main__":
    main()
