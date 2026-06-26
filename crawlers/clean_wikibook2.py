#!/usr/bin/env python3
"""Cleanup pass for the batch-2 wikisource staging JSONs, driven by the audit:
 - strip Wikisource editorial-annotation lines (ప్రక్షిప్తమని తోఁచెడు / …గానఁబడదయ్యెడు)
 - strip colophon prose (… ప్రణీతంబైన … మహాప్రబంధంబునందు …) merged into verses
 - strip trailing prose captions in the చాటు anthologies (attribution / "—"-ended)
 - strip stray symbols (` _ · and a leading ". ")
 - DROP the two dramas (all stage-direction/dialogue prose, no padyalu)
 - శృంగారపంచకము: drop its inner కాళిదాసప్రహసనమ్ play chapter; fix literary form
Then reuses clean_json's markup/apparatus strip + canonical chapter order + global id.
"""
from __future__ import annotations

import glob
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import clean_json as cj  # noqa: E402

OUT = Path(__file__).resolve().parent / "wikibook2_json"
DROP = {"sitavanavasamu_duvvuri_ramireddy", "kalidasaprahasanam"}      # dramas
CHATU = {"chatupadyamanimanjari_veturi_prabhakara", "chatupadyaratnakaramu_deepala_picchayya"}

_ANNOT = re.compile(r"ప్రక్షిప్త|తోఁచెడు|గానఁబడదయ్యెడు|ఈస్థలంబున|గ్రంథపాతము|^\s*పా\.\s")
_COLOPHON = re.compile(r"ప్రణీతంబైన|మహాప్రబంధంబున|అను.{0,30}ప్రబంధంబునందు|ఇది శ్రీ.*ప్రణీత")
_CAPTION = re.compile(r"జెప్పిన|జెప్పెను|చెప్పిన|రచించె|వ్రాసిన|^ఈకవి|లేఖకుఁ?డు|నుగూర్చి|క్రింది|^[0-9]+\s*\.")
_EMDASH = re.compile(r"[—–]\s*$")
_SYM = re.compile(r"[`_·​‌]")
_DRAMA = re.compile(r"^[^:：\s]{1,8}\s*[:：]|\[.*\]|ప్రవేశించి|నిష్క్రమించి")  # speaker:/stage dir


def _clean(s: str) -> str:
    s = _SYM.sub("", s)
    s = re.sub(r'^[".\s]*\.\s+', "", s)
    return re.sub(r"\s+", " ", s).strip()


def _is_noise(s: str, chatu: bool) -> bool:
    if _ANNOT.search(s) or _COLOPHON.search(s):
        return True
    return bool(chatu and (_CAPTION.search(s) or _EMDASH.search(s)))


def process(slug: str) -> None:
    d = json.loads((OUT / f"{slug}.json").read_text())
    chatu = slug in CHATU
    if slug == "sringarapanchakamu_collection":
        d["poems"] = [p for p in d["poems"] if p.get("chapter") != "కాళిదాసప్రహసనమ్"]
        d["literary_form_telugu"] = "శృంగార సంకలనము"
    out = []
    for p in d["poems"]:
        lines = [_clean(x) for x in p.get("lines_telugu", [])]
        lines = [x for x in lines if x and not _is_noise(x, chatu)]
        lines = [x for x in lines if len(x) >= 2]
        if len(lines) < 2 or len(lines) > 16:
            continue
        if sum(1 for x in lines if _DRAMA.search(x)) >= max(1, len(lines) / 2):  # drama prose
            continue
        p["lines_telugu"] = lines
        out.append(p)
    d["poems"] = out
    (OUT / f"{slug}.json").write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    cj.OUT = OUT
    cj.SET_OCR, cj.CLEAR_OCR, cj.SONG_SLUGS = set(), set(), set()
    slugs = sorted(Path(f).stem for f in glob.glob(str(OUT / "*.json")))
    ta = 0
    for s in slugs:
        if s in DROP:
            (OUT / f"{s}.json").unlink()
            print(f"  DROPPED {s} (drama)")
            continue
        process(s)               # batch-2 specific strips + drops
        r = cj.process(s)        # clean_json: markup/apparatus, reorder, dedup, global id
        ta += r["after"]
        print(f"  {r['after']:5d}  {s[:46]}")
    print(f"\nTOTAL: {ta} padyalu across {len(slugs) - len(DROP)} books")


if __name__ == "__main__":
    main()
