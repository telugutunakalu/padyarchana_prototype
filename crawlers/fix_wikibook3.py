#!/usr/bin/env python3
"""Targeted repair pass for batch-3, driven by the fidelity audit's confirmed,
deterministically-detectable defect families:

  A. SEAM-MERGE  — two verses fused because the first ends with an embedded
     padyam-number ("...కామినుల్. 59") and the parser didn't break there.
     Split on every line that ends in a verse-number; the trailing number
     becomes that verse's padyam_number; a leading meter-abbrev on the next
     verse is read into its Chandassu.
  B. ATTRIBUTION / RESIDUE TAIL — anthology poet-sigla "(జ)", editorial
     brackets "[…]", back-refs "↑", glyph-rule runs, "శ్రీ శ్రీ శ్రీ",
     and "=" word-gloss footnotes captured as verse lines → strip/drop.
  C. HEADING TAIL — a prose section-heading (dash-terminated or
     "…వర్ణనము/…కథ/…ఉదాహరణము") appended as the last line of a >2-line verse.
  + metadata fixes (నవనాథ year, విష్ణుపురాణము author) and dropping the
    unsalvageable garbled శ్రీవేంకటేశ్వరస్తుతిరత్నమాల.
Couplet (ద్విపద/ఉత్కళిక) works are exempt from A/C (2-line by construction).
"""
from __future__ import annotations

import glob
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import text_to_json as t  # noqa: E402

OUT = Path(__file__).resolve().parent / "wikibook3_json"
DWIPADA = {"navanaathacharitra_gaurana", "saugamdhikaprasavaapaharanamu_gopaalaraaju",
           "shriinivaasavilaasasevadhi_vemkataarya", "raajayogasaaramu_vemgamaamba",
           "shashikala_baapiraaju"}
DROP = {"shriivemkateshvarastutiratnamaala_kavulu"}

_SEAM = re.compile(r"^(.*[ఀ-౿][.।॥]?)\s+([0-9౦-౯]{1,4})\s*[.।॥]?\s*$")
_LEADMARK = re.compile(r"^(" + t._MARK_ALT + r")\s*[.,।]\s*")
_ATTR_TAIL = re.compile(r"\([ఀ-౿]{1,5}\)\s*$|↑.*$|\[[^\]]*\]\s*$|[ᛟ]{2,}.*$|శ్రీ\s+శ్రీ\s+శ్రీ.*$")
_GLOSS = re.compile(r"[ఀ-౿]\s*=\s*[ఀ-౿]")                         # footnote word-gloss
_HEADING = re.compile(r"(వర్ణనము?|కథ|ఉదాహరణము?|షష్ఠ్యంత[ఀ-౿]*|ప్రారంభము?)\s*[.—–:-]*\s*$|[—–]\s*$")
_TEL = re.compile(r"[ఀ-౿]")


def _to_int(s):
    m = "౦౧౨౩౪౫౬౭౮౯"
    return int("".join(str(m.index(c)) if c in m else c for c in s))


def seam_split(p):
    """Re-segment one possibly-merged poem into its constituent verses."""
    lt = p["lines_telugu"]
    verses, buf = [], []
    for ln in lt:
        m = _SEAM.match(ln)
        buf.append(m.group(1).strip() if m else ln)
        if m:
            verses.append((buf[:], _to_int(m.group(2))))
            buf = []
    if buf:
        verses.append((buf, None))
    if len(verses) <= 1:                       # nothing to split
        return [p]
    out = []
    for k, (lines, num) in enumerate(verses):
        meter = p["Chandassu"]
        if k > 0 and lines:                    # split-off verse: read its leading marker
            mk = _LEADMARK.match(lines[0])
            if mk:
                meter = t.MARKERS.get(mk.group(1), "unknown")
                lines[0] = lines[0][mk.end():].strip()
            else:
                meter = "unknown"
        lines = [x for x in lines if x.strip()]
        if len(lines) < 2 or not any(_TEL.search(x) for x in lines):
            continue
        out.append({**p, "lines_telugu": lines, "Chandassu": meter, "padyam_number": num if num else p.get("padyam_number")})
    return out or [p]


def strip_tails(p, is_dw):
    lines = []
    for ln in p["lines_telugu"]:
        s = _ATTR_TAIL.sub("", ln).strip()
        if _GLOSS.search(s):                    # whole line is a gloss footnote
            continue
        if s:
            lines.append(s)
    # heading tail (non-couplet, >2 lines): drop a trailing heading/dash line
    if not is_dw and len(lines) > 2 and _HEADING.search(lines[-1]):
        lines = lines[:-1]
    p["lines_telugu"] = [x for x in lines if len(x) >= 2]
    return p


def process(slug):
    fp = OUT / f"{slug}.json"
    d = json.loads(fp.read_text())
    is_dw = slug in DWIPADA
    out = []
    for p in d["poems"]:
        segs = [p] if is_dw else seam_split(dict(p))
        for s in segs:
            s = strip_tails(s, is_dw)
            if len(s["lines_telugu"]) >= 2:
                out.append(s)
    for i, p in enumerate(out, 1):
        p["id"] = i
    d["poems"] = out
    # metadata fixes
    if slug == "navanaathacharitra_gaurana" and str(d.get("year", "")).strip() in ("}}", "", "unknown"):
        d["year"] = "unknown"
    if slug.startswith("vishnupuraanamu") and d.get("author_telugu") in (None, "unknown"):
        d["author_telugu"] = "కలిదిండి భావనారాయణ"
    fp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(out)


def main():
    slugs = sorted(Path(f).stem for f in glob.glob(str(OUT / "*.json")))
    total = 0
    for s in slugs:
        if s in DROP:
            (OUT / f"{s}.json").unlink()
            print(f"  DROPPED {s} (garbled multi-script OCR, 12 records)")
            continue
        n = process(s)
        total += n
    print(f"\nTOTAL after repair: {total} padyalu across {len(slugs) - len(DROP)} books")


if __name__ == "__main__":
    main()
