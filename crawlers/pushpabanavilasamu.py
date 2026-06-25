#!/usr/bin/env python3
"""Structure పుష్పబాణవిలాసము (బిరుదరాజ శేషాద్రిరాజు, 1893) from Wikisource.

A single transcluded page that interleaves three things, in repeating blocks:
  * అ. …   — prose annotation describing the upcoming verse (SKIPPED)
  * శ్లో. … — the Sanskrit source śloka (Telugu script)
  * ఉ./చ./తే./క. … — the Telugu rendering padyam

There are no per-verse numbers, so a verse otherwise absorbs the following prose;
we therefore terminate a verse at any line that opens with a non-meter marker
(అ., శ్రీ, …) and skip those prose runs. Both the ślokas and the Telugu padyalu
are kept (distinguished by Chandassu); only the prose and front matter are dropped.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wikisource_crawler as w  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "padyalu_json_data"
WORK = "పుష్పబాణవిలాసము"

MARKERS = {
    "శ్లో": "శ్లోకము", "సీ": "సీసము", "ఆ": "ఆటవెలది", "తే": "తేటగీతి",
    "గీ": "గీతము", "క": "కందము", "చ": "చంపకమాల", "ఉ": "ఉత్పలమాల",
    "మ": "మత్తేభవిక్రీడితము", "శా": "శార్దూలవిక్రీడితము", "వ": "వచనము",
    "మత్త": "మత్తకోకిల", "మా": "మాలిని",
}
_ALT = "|".join(sorted(MARKERS, key=len, reverse=True))
# a line opening with <token>. or <token>॥ — token is a meter abbrev OR anything
# else (అ., శ్రీ, …) which we treat as a prose/section start.
MARK = re.compile(rf"^({_ALT}|[ఀ-౿]{{1,4}})\s*[.॥]\s*(.*)$")


def _clean(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip(" .,-।॥|!").strip()


# max padams per meter. Some prose annotations are written "అ " (no period) and
# slip past the marker; the dedication/colophon trail header lines. In every case
# the real padams come first, so we keep only the meter's padam count.
_CAP = {"శ్లోకము": 6, "సీసము": 13, "వచనము": 12}


def _cap(chandassu: str) -> int:
    return _CAP.get(chandassu, 4)


def parse(text: str) -> list[dict]:
    blocks: list[tuple[str, list[str]]] = []
    cur: tuple[str, list[str]] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = MARK.match(line)
        if m:
            tok, rest = m.group(1), m.group(2).strip()
            if tok in MARKERS:                      # a verse begins
                if cur:
                    blocks.append(cur)
                cur = (tok, [rest] if rest else [])
                continue
            # non-meter marker (అ. prose, శ్రీ, …) — end verse, skip the run
            if cur:
                blocks.append(cur)
            cur = None
            continue
        if cur is not None:                          # a padam line of the verse
            cur[1].append(line)
    if cur:
        blocks.append(cur)

    out: list[dict] = []
    for tok, raw_lines in blocks:
        chandassu = MARKERS[tok]
        lines = [_clean(x) for x in raw_lines]
        lines = [x for x in lines if len(x) >= 3][: _cap(chandassu)]
        if not lines:
            continue
        out.append({
            "lines_telugu": lines,
            "Chandassu": chandassu,
            "padyam_number": "unknown",
            "bhavam": None,
            "prathipadartham": None,
        })
    return out


def main() -> None:
    text = w.fetch_rendered(WORK)
    poems = parse(text)
    poems = [{"id": i, **p} for i, p in enumerate(poems, 1)]
    rec = {
        "shatakam_title_telugu": WORK,
        "author_telugu": "బిరుదరాజ శేషాద్రిరాజు",
        "year": 1893,
        "literary_form_telugu": "కావ్యము",
        "source_url": "https://te.wikisource.org/wiki/" + WORK,
        "poems": poems,
    }
    OUT.mkdir(exist_ok=True)
    fp = OUT / "pushpabanavilasamu_birudaraja_seshadriraju.json"
    fp.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"-> {fp.name} ({len(poems)} poems)")


if __name__ == "__main__":
    main()
