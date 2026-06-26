#!/usr/bin/env python3
"""Parse the శతకసాహిత్యం blog śatakam posts (crawlers/shatakashityam_raw/*.json)
into padyarchana JSON — one file per śatakam.

Each post body is one full śatakam. Handles the four layouts seen on the blog:
  1. numbered + per-padyam meter:  "1. శా. …"
  2. numbered + header-declared meter:  "(కందపద్య శతకము)" then "1. …"
  3. numbered + no meter:  "1. …"            → Chandassu unknown
  4. marker-only (un-numbered):  "మ. …", "శా. …"  → via text_to_json markers

Author comes from the title ("… శతకము - <author>"), cross-checked with the
post's Telugu label; "రచయిత తెలియదు"/missing → unknown. Per-padyam meter is the
explicit one if present, else the header meter, else unknown. Verse text is
copied verbatim (no transcription, no normalization)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import text_to_json as t  # noqa: E402

RAW = Path(__file__).resolve().parent / "shatakashityam_raw"
OUT = Path(__file__).resolve().parent / "shatakashityam_json"   # staging; onboard later

ABBR = {"శా": "శార్దూలవిక్రీడితము", "మ": "మత్తేభవిక్రీడితము", "క": "కందము", "కం": "కందము",
        "చ": "చంపకమాల", "చం": "చంపకమాల", "ఉ": "ఉత్పలమాల", "తే": "తేటగీతి", "ఆ": "ఆటవెలది",
        "సీ": "సీసము", "గీ": "గీతము", "వ": "వచనము", "మత్త": "మత్తకోకిల", "మాలి": "మాలిని",
        "స్రగ్ధ": "స్రగ్ధర", "ఉత్స": "ఉత్సాహ"}
_AB = "|".join(sorted(ABBR, key=len, reverse=True))
HDR = {"కంద": "కందము", "సీస": "సీసము", "ఆటవెలది": "ఆటవెలది", "తేటగీతి": "తేటగీతి",
       "చంపకమాల": "చంపకమాల", "ఉత్పలమాల": "ఉత్పలమాల", "మత్తేభ": "మత్తేభవిక్రీడితము",
       "శార్దూల": "శార్దూలవిక్రీడితము", "ఆటవెల": "ఆటవెలది"}

# number anchor: "12." or "12)" optionally followed by a meter abbrev (period OR space)
_NUM = re.compile(r"^\s*(\d+)\s*[.)]\s*(?:(" + _AB + r")\s*[.\s])?\s*(.*)$")
_MARK = re.compile(r"^\s*(" + _AB + r")\s*\.\s+(.*)$")          # un-numbered "మ. …"
# NB: \w does NOT match Telugu combining marks (ం ్ ా …) — use the Telugu block.
_ENDWORD = re.compile(r"^\s*(సమాప్త|సంపూర్ణ|పరిసమాప్త)[ఀ-౿]*\s*[.।॥]*\s*$")
_COLOPHON = re.compile(r"శతక[ఀ-౿]*\s+(సమాప్త|సంపూర్ణ)|ార్పణమ|అర్పణమస్తు|ఓం\s*తత్సత్|పాఠ[ఀ-౿]*తర")
_DIVIDER = re.compile(r"^\s*[-–—]\s*:.*:\s*[-–—]\s*$|^\s*[-=*•]{3,}\s*$")
_GAPNOTE = re.compile(r"దొరక(లేదు|లే\b)|లభించలేదు|నుండి.{0,8}వరకు.{0,14}లేదు|లభ్యం\s*కాలేదు")
_HDRMETER = re.compile(r"\((కంద|సీస|ఆటవెల\w*|తేటగీతి|చంపకమాల|ఉత్పలమాల|మత్తేభ\w*|శార్దూల\w*)\s*పద్య")
_UNKNOWN_AUTH = re.compile(r"తెలియదు|తెలీదు|అజ్ఞాత|unknown", re.I)
_TEL = re.compile(r"[ఀ-౿]")


def _is_noise(ln: str) -> bool:
    ln = ln.strip()
    return bool(_ENDWORD.match(ln) or _COLOPHON.search(ln) or _DIVIDER.match(ln) or _GAPNOTE.search(ln))


def _is_header(ln: str, name: str, author: str) -> bool:
    ln = ln.strip()
    if ln in (name, author):
        return True
    if name and name in ln and len(ln) <= len(name) + 4:
        return True
    if author and author != "unknown" and author.split()[0] in ln and "శతక" not in ln and len(ln) < len(author) + 22:
        return True
    if re.match(r"^[\(（].*(పద్య|శతక).*[\)）]\s*$", ln):
        return True
    return bool(re.match(r"^\s*(--|—|శతకకర్త|రచయిత)", ln))


def _blocks(raw: list[str]) -> list[list[str]]:
    """Group lines into padyam-blocks: padyalu are separated by 2+ blank lines,
    lines within a padyam by single blanks."""
    blocks, cur, blank = [], [], 0
    for ln in raw:
        if ln.strip():
            if blank >= 2 and cur:
                blocks.append(cur)
                cur = []
            cur.append(re.sub(r"\s+", " ", ln).strip())
            blank = 0
        else:
            blank += 1
    if cur:
        blocks.append(cur)
    return blocks


def header_meter(lines: list[str]) -> str | None:
    m = _HDRMETER.search("\n".join(lines[:6]))
    if not m:
        return None
    for k, v in HDR.items():
        if m.group(1).startswith(k):
            return v
    return None


def author_from(title: str, labels: list[str]) -> str:
    # title: "<śatakam> - <author> [(year)]"  OR  "<śatakam>  <author>"
    tail = re.split(r"\s[-–]\s|\s[-–]", title, 1)
    cand = tail[1].strip() if len(tail) > 1 else ""
    cand = re.sub(r"\s*\([^)]*\)", "", cand).strip(" .-–—")
    if cand and not _UNKNOWN_AUTH.search(cand):
        return cand
    if _UNKNOWN_AUTH.search(title):
        return "unknown"
    # fall back to a Telugu label that isn't the śatakam-name / category tag
    for lab in labels:
        if lab.isascii() or "శతక" in lab or "సాహిత్య" in lab:
            continue
        return lab
    return "unknown"


def _mk(lines: list[str], meter: str) -> dict:
    return {"lines_telugu": [x for x in lines if x.strip()], "Chandassu": meter,
            "bhavam": None, "prathipadartham": None}


_GITA = {"గీ", "తే", "ఆ"}


def parse_numbered(blocks: list[list[str]], default_meter: str | None) -> list[dict]:
    """Numbered śatakam. Only the "N." line starts a padyam; a single padyam may
    span several blank-delimited blocks (సీస-body→గీత, or a vrutta split in two),
    so any non-numbered block before the next number is appended to the current
    padyam while it is still incomplete (<10 lines). Un-numbered blocks before the
    first number are standalone invocatory padyalu."""
    poems: list[dict] = []
    seen = False
    for block in blocks:
        if _NUM.match(block[0]):
            seen = True
            idx = [i for i, ln in enumerate(block) if _NUM.match(ln)]
            for j, s in enumerate(idx):
                e = idx[j + 1] if j + 1 < len(idx) else len(block)
                m = _NUM.match(block[s])
                ab, first = m.group(2), m.group(3).strip()
                pl = ([first] if first else []) + block[s + 1:e]
                if len([x for x in pl if x.strip()]) >= 2:
                    poems.append(_mk(pl, ABBR[ab] if ab in ABBR else (default_meter or "unknown")))
            continue
        if not (len(block) >= 1 and sum(_TEL.search(x) is not None for x in block) >= 1):
            continue
        mm = _MARK.match(block[0])
        lines = ([mm.group(2)] + block[1:]) if (mm and mm.group(1) in ABBR) else block
        lines = [x for x in lines if x.strip()]
        if not seen:                                   # invocatory, before "1."
            if len(lines) >= 2:
                poems.append(_mk(lines, default_meter or "unknown"))
        elif poems and len(poems[-1]["lines_telugu"]) < 10:   # continuation (గీత / split half)
            poems[-1]["lines_telugu"] += lines
            if poems[-1]["Chandassu"] == "unknown" and mm and mm.group(1) in _GITA:
                poems[-1]["Chandassu"] = "సీసము"
        elif len(lines) >= 2:                          # standalone concluding padyam
            poems.append(_mk(lines, ABBR[mm.group(1)] if (mm and mm.group(1) in ABBR) else (default_meter or "unknown")))
    return poems


def parse_one(rec: dict) -> dict:
    title = rec["title"].strip()
    name = re.split(r"\s[-–]\s|\s[-–]", title, 1)[0].strip()
    author = author_from(title, rec.get("labels", []))
    raw = rec["body_text"].splitlines()
    flat = [ln.strip() for ln in raw if ln.strip()]
    default_meter = header_meter(flat[:6])
    # blank-delimited blocks, with header/noise lines stripped
    blocks = []
    for bi, block in enumerate(_blocks(raw)):
        block = [ln for ln in block if not _is_noise(ln)]
        if bi < 4:
            block = [ln for ln in block if not _is_header(ln, name, author)]
        block = [ln for ln in block if ln.strip()]
        if block:
            blocks.append(block)
    n_num = sum(1 for ln in flat if _NUM.match(ln))
    n_mark = sum(1 for ln in flat if _MARK.match(ln))
    if n_num >= 15:
        poems = parse_numbered(blocks, default_meter)
    elif n_mark >= 15:                       # marker-only layout (నారాయణ-style)
        poems = t.parse_padyalu("\n".join(ln for b in blocks for ln in b))
        for p in poems:
            if p.get("Chandassu") in (None, "unknown", "వచనము") and default_meter:
                p["Chandassu"] = default_meter
            p.setdefault("bhavam", None)
            p.setdefault("prathipadartham", None)
    else:                                    # blank-delimited, un-numbered
        poems = [_mk(b, default_meter or "unknown") for b in blocks
                 if len(b) >= 2 and sum(_TEL.search(x) is not None for x in b) >= 2]
    for i, p in enumerate(poems, 1):
        p["id"] = i
        p["padyam_number"] = i
    return {
        "shatakam_title_telugu": name or title,
        "author_telugu": author_from(title, rec.get("labels", [])),
        "year": "unknown",
        "literary_form_telugu": "శతకము",
        "source_url": rec.get("url"),
        "note": "Crawled from the శతకసాహిత్యం blog (shatakashityam.blogspot.com).",
        "poems": poems,
    }


def slugify(rec: dict) -> str:
    asc = [l for l in rec.get("labels", []) if l.isascii() and len(l) > 3 and l != "SatakasAhityaM"]
    base = next((l for l in asc if "Satak" in l), None) or (asc[0] if asc else rec["title"])
    return (re.sub(r"[^a-z0-9]+", "_", base.lower()).strip("_") or "shatakam") + "_shatakashityam"


def main():
    OUT.mkdir(exist_ok=True)
    results = []
    used: set = set()
    for f in sorted(RAW.glob("*.json")):
        if f.name == "manifest.json":
            continue
        rec = json.loads(f.read_text())
        out = parse_one(rec)
        slug = slugify(rec)
        if slug in used:                       # guarantee unique filenames
            k = 2
            while f"{slug.removesuffix('_shatakashityam')}_{k}_shatakashityam" in used:
                k += 1
            slug = f"{slug.removesuffix('_shatakashityam')}_{k}_shatakashityam"
        used.add(slug)
        (OUT / f"{slug}.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        results.append((slug, out["shatakam_title_telugu"], out["author_telugu"], len(out["poems"])))
    results.sort(key=lambda r: r[3])
    for slug, name, auth, n in results:
        print(f"  {n:3d}  {name[:30]:30s} | {auth[:24]:24s} | {slug[:30]}")
    print(f"\nTOTAL: {sum(r[3] for r in results)} padyalu across {len(results)} śatakams")


if __name__ == "__main__":
    main()
