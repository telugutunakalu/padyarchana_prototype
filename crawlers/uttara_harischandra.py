#!/usr/bin/env python3
"""Salvage padyalu from ఉత్తరహరిశ్చంద్రోపాఖ్యానము (తక్కెళ్ళపాటి లింగన, 1891).

This Wikisource text is an UNPROOFREAD OCR of a 1891 print: each ఆశ్వాసము
renders as one long garbled paragraph with verses run together — but the meter
markers (శా॥ సీ॥ చ॥ ఉ॥ మ॥ క॥ …) and trailing verse numbers survive. We split on
those markers, treat each span as a padyam, split it into padams on the inline
dandas (| ! । ॥), strip page-header noise, and keep only discernible verses.

The verse *text* remains OCR-garbled (that's inherent to the source); what is
reliably recoverable is the meter, the padam segmentation, the verse number, and
the ఆశ్వాసము. Fragments too short/garbled to be a verse are dropped.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wikisource_crawler as w  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "padyalu_json_data"
WORK = "ఉత్తరహరిశ్చంద్రోపాఖ్యానము"
CHAPTERS = ["ప్రథమాశ్వాసము", "ద్వితీయాశ్వాసము", "తృతీయాశ్వాసము", "చతుర్థాశ్వాసము"]

METER = {
    "శా": "శార్దూలవిక్రీడితము", "సీ": "సీసము", "మత్త": "మత్తకోకిల",
    "తే": "తేటగీతి", "గీ": "గీతము", "మాలి": "మాలిని", "స్రగ్ధ": "స్రగ్ధర",
    "చ": "చంపకమాల", "ఉ": "ఉత్పలమాల", "మ": "మత్తేభవిక్రీడితము",
    "క": "కందము", "ఆ": "ఆటవెలది", "వ": "వచనము",
}
_ALT = "|".join(sorted(METER, key=len, reverse=True))
# a meter abbrev that is NOT part of a larger Telugu word (lookbehind), followed
# by a danda (॥ or one/two pipes). Catches " సీ॥ ", "3. చ|| ", " క| ".
MARK = re.compile(rf"(?<![ఀ-౿])({_ALT})\s*(?:॥|\|\|?)")
PADAM = re.compile(r"[|!।॥]+")
NUM = re.compile(r"[0-9౦-౯]+")
# repeated running-header / spine noise to delete before splitting
HEADER = re.compile(
    r"ఉత్తరహరిశ్చంద్రోపాఖ్యానము[.\s]*|పద్యకావ్యము[.\s]*|శ్రీ\s*శ్రీధ\S*\s*ముః?[.\s]*"
)
# a "line" that is really just OCR rubble: too short or mostly non-Telugu
_TEL = re.compile(r"[ఀ-౿]")


# running-header / section-label tokens that leak into verse lines
_LEAK = re.compile(
    r"కథాప్రారంభము|కథారంభము|పద్యకావ్యము|ఉత్తరహరిశ్చంద్రోపాఖ్యానము|అవతారిక"
    r"|ప్రథమాశ్వాసము|ద్వితీయాశ్వాసము|తృతీయాశ్వాసము|చతుర్థాశ్వాసము"
    r"|[A-Za-z]+|[+*]\d*"
)


def _clean_line(s: str) -> str:
    s = _LEAK.sub(" ", s)
    s = re.sub(r"[*+•—–]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s[0-9౦-౯]+(?=\s|$)", " ", s)  # OCR-displaced verse numbers mid-line
    s = re.sub(r"\s+", " ", s).strip(" .,-॥|!।0123456789౦౧౨౩౪౫౬౭౮౯")
    return s.strip()


def _telugu_ratio(s: str) -> float:
    nonspace = [c for c in s if not c.isspace()]
    return len(_TEL.findall(s)) / len(nonspace) if nonspace else 0.0


# expected padam (line) count per meter. The OCR splits on inline dandas, which
# align with padams; 4-padam vruttas must give EXACTLY 4 clean lines (anything
# else is merged/fragmented). వచనము (prose) is dropped entirely as unreliable.
PADAM_RANGE = {"సీసము": (6, 13)}
_DEFAULT_RANGE = (4, 4)  # 4-padam vruttas (కంద/చంప/ఉత్పల/శార్దూల/మత్తేభ/గీత…)
_DROP_METERS = {"వచనము"}


def parse_chapter(text: str, chapter: str) -> list[dict]:
    text = HEADER.sub(" ", text)
    ms = list(MARK.finditer(text))
    poems: list[dict] = []
    for i, m in enumerate(ms):
        start = m.end()
        end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        block = text[start:end]
        # the trailing number just before the next marker is the verse number
        nums = NUM.findall(block)
        number = int(nums[-1]) if nums and nums[-1].isdigit() else "unknown"
        # drop that trailing "॥ <num> ." tail, then split into padams
        body = re.sub(r"[॥|।\s]*[0-9౦-౯]+[.\s]*$", "", block)
        lines = [_clean_line(p) for p in PADAM.split(body)]
        # keep only substantial, almost-entirely-Telugu padam lines
        lines = [ln for ln in lines if len(ln) >= 6 and _telugu_ratio(ln) >= 0.85]
        chandassu = METER[m.group(1)]
        # --- tightened discernibility ---
        if number == "unknown" or chandassu in _DROP_METERS:
            continue
        lo, hi = PADAM_RANGE.get(chandassu, _DEFAULT_RANGE)
        if not (lo <= len(lines) <= hi):  # line count must fit the meter exactly
            continue
        if sum(len(ln) for ln in lines) < 50:
            continue
        # reject blocks with a runaway merged line (two padyalu fused by a
        # dropped marker) — longest line shouldn't dwarf the rest
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
        "author_telugu": "తక్కెళ్ళపాటి లింగన",
        "year": 1891,
        "literary_form_telugu": "పద్యకావ్యము",
        "source_url": "https://te.wikisource.org/wiki/" + WORK,
        "note": "Salvaged from an unproofread OCR; verse text is OCR-garbled.",
        "poems": all_poems,
    }
    OUT.mkdir(exist_ok=True)
    fp = OUT / "uttara_harischandropakhyanamu_takkellapati_lingana.json"
    fp.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n-> {fp.name} ({len(all_poems)} padyalu)")


if __name__ == "__main__":
    main()
