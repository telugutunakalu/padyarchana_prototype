#!/usr/bin/env python3
"""Cleanup pass for the batch-3 wikisource staging JSONs (crawlers/wikibook3_json/).
Mirrors batch-2's strips (editorial annotations, merged colophon prose, stray
symbols) then reuses clean_json's markup/apparatus strip + canonical chapter
order + exact dedup + global id.

ద్విపద / ఉత్కళిక works are already deduped+numbered upstream; they skip the
drama-prose heuristic (a 2-line couplet could trip it) but still get the safe
line-level strips and clean_json's exact-dedup (which leaves unique couplets).

Works left with <10 padyalu (modern free-verse, garbled OCR with nothing
salvageable) are dropped — and reported, never silently.
"""
from __future__ import annotations

import glob
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import clean_json as cj  # noqa: E402

OUT = Path(__file__).resolve().parent / "wikibook3_json"
DWIPADA = {"navanaathacharitra_gaurana", "saugamdhikaprasavaapaharanamu_gopaalaraaju",
           "shriinivaasavilaasasevadhi_vemkataarya", "raajayogasaaramu_vemgamaamba",
           "shashikala_baapiraaju"}
MIN_PADYALU = 10

_ANNOT = re.compile(r"ప్రక్షిప్త|తోఁచెడు|గానఁబడదయ్యెడు|ఈస్థలంబున|గ్రంథపాతము|^\s*పా\.\s")
_COLOPHON = re.compile(r"ప్రణీతంబైన|మహాప్రబంధంబున|అను.{0,30}ప్రబంధంబునందు|ఇది శ్రీ.*ప్రణీత")
_SYM = re.compile(r"[`_·​‌]")
_DRAMA = re.compile(r"^[^:：\s]{1,8}\s*[:：]|\[.*\]|ప్రవేశించి|నిష్క్రమించి")


def _clean(s: str) -> str:
    s = _SYM.sub("", s)
    s = re.sub(r'^[".\s]*\.\s+', "", s)
    return re.sub(r"\s+", " ", s).strip()


def _is_noise(s: str) -> bool:
    return bool(_ANNOT.search(s) or _COLOPHON.search(s))


def process(slug: str) -> None:
    d = json.loads((OUT / f"{slug}.json").read_text())
    is_dw = slug in DWIPADA
    out = []
    for p in d["poems"]:
        lines = [_clean(x) for x in p.get("lines_telugu", [])]
        lines = [x for x in lines if x and not _is_noise(x)]
        lines = [x for x in lines if len(x) >= 2]
        if len(lines) < 2:
            continue
        if not is_dw and len(lines) > 16:                # apparatus blob (couplets exempt)
            continue
        if not is_dw and sum(1 for x in lines if _DRAMA.search(x)) >= max(1, len(lines) / 2):
            continue
        p["lines_telugu"] = lines
        out.append(p)
    d["poems"] = out
    (OUT / f"{slug}.json").write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    cj.OUT = OUT
    cj.SET_OCR, cj.CLEAR_OCR, cj.SONG_SLUGS = set(), set(), set()
    slugs = sorted(Path(f).stem for f in glob.glob(str(OUT / "*.json")))
    kept, dropped, total = [], [], 0
    for s in slugs:
        process(s)
        r = cj.process(s)
        if r["after"] < MIN_PADYALU:
            dropped.append((s, r["after"]))
            (OUT / f"{s}.json").unlink()
            continue
        kept.append((s, r["after"], r["flag"]))
        total += r["after"]
    for s, n, flag in sorted(kept, key=lambda x: -x[1]):
        print(f"  {n:5d}  {s[:48]:48s} {('['+flag+']') if flag else ''}")
    print(f"\nDROPPED (<{MIN_PADYALU} padyalu): {len(dropped)}")
    for s, n in dropped:
        print(f"   {n:3d}  {s}")
    print(f"\nTOTAL: {total} padyalu across {len(kept)} books (dropped {len(dropped)})")


if __name__ == "__main__":
    main()
