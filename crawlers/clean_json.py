#!/usr/bin/env python3
"""Post-process the crawled Wikisource padyalu JSONs to fix the systemic defects
found in the verification audit, deterministically and in one pass:

  1. strip MediaWiki markup that leaked into lines (<ref>/<poem>, {{…}} templates,
     దస్త్రం:/File: links, stray Latin OCR scars / page anchors);
  2. drop critical-edition footnote apparatus lines (పాఠాంతరాలు / వ్రాఁతప్రతుల …);
  3. strip the trailing source verse-number glued to the last padam and use it to
     fill padyam_number when it was 'unknown';
  4. drop entries emptied by the above, and drop apparatus-dump "mega-blobs";
  5. dedupe exact multi-line page-overlap duplicates (keep first);
  6. re-sequence poems into canonical ఆశ్వాసము / కాండము order and assign a single
     global running id (the crawl listed chapters alphabetically);
  7. correct OCR-sourced flags (set where genuinely OCR-garbled, clear false positive).

Usage:  clean_json.py [slug ...]   (no args → all books in keep_list.json)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "padyalu_json_data"

# ---- canonical chapter ordering --------------------------------------------
_ASV = "ప్రథమ ద్వితీయ తృతీయ చతుర్థ చతుర్ధ పంచమ షష్ఠ సప్తమ అష్టమ నవమ దశమ ఏకాదశ ద్వాదశ త్రయోదశ చతుర్దశ".split()
_ASV_ORD = {n: i for i, n in enumerate(_ASV, 1)}
# చతుర్థ/చతుర్ధ are spelling variants of the 4th
_ASV_ORD["చతుర్ధ"] = _ASV_ORD["చతుర్థ"] = 4
_KANDA = "బాలకాండ అయోధ్యాకాండ ఆరణ్యకాండ కిష్కింధాకాండ సుందరకాండ యుద్ధకాండ ఉత్తరకాండ".split()
_KANDA_ORD = {n: i for i, n in enumerate(_KANDA, 1)}
_PARVA = {"విరాటపర్వ": 1, "ఉద్యోగపర్వ": 2}
_BHAGA = {"పూర్వభాగ": 0, "ఉత్తరభాగ": 1}


def chapter_key(ch, fallback: int):
    """Sort key putting chapters in reading order. fallback = file position so
    unknown labels keep their original relative order."""
    if not ch:
        return (0, 0, 0, 0, fallback)
    ch = str(ch)
    parva = next((v for k, v in _PARVA.items() if k in ch), 0)
    bhaga = next((v for k, v in _BHAGA.items() if k in ch), 0)
    kanda = next((v for k, v in _KANDA_ORD.items() if k in ch), 0)
    asv = next((v for n, v in _ASV_ORD.items() if n in ch), 0)
    sarga = 0
    m = re.search(r"సర్గ\s*([0-9౦-౯]+)", ch)
    if m:
        sarga = int(re.sub(r"\D", "", m.group(1)) or 0)
    return (parva, bhaga, kanda, asv or sarga, fallback)


# ---- line-level cleaning ----------------------------------------------------
_TAG = re.compile(r"</?ref[^>]*>|</?poem[^>]*>|\{\{[^}]*\}\}|&lt;/?ref&gt;")
_LINK = re.compile(r"దస్త్రం\s*:\S*|\bFile\s*:\S*|\S*\.pdf\S*")
_LATIN = re.compile(r"[A-Za-z]+")               # OCR scars, page anchors (l62, I61, Ks), ref residue
_APPARATUS = re.compile(
    r"వ్రాఁతప్రతుల|వ్రా\.\s*ప్ర|అ\.\s*ప్ర|మాఱుగా|వఱకుఁ\s*గల|^\s*[0-9౦-౯]+\s*మొదలుగా"
    r"|పాఠాంతర|అని\s*పా\.|^\s*పుట\s*[0-9౦-౯]+\s*$|గ్రంథపాతము|చదువ(దగదు|వలెను)")
_RULE = re.compile(r"^[-—–_\s.|]+$")
_PAGEANCHOR = re.compile(r"^\s*(పుట\s*[0-9౦-౯]+|[0-9౦-౯]+\s*వ?\s*పుట)\s*$")


def _is_apparatus(s: str) -> bool:
    return bool(_APPARATUS.search(s)) or bool(_RULE.match(s)) or s.strip() in ("సంపూర్ణము.", "సమాప్తము.")


def _clean_line(s: str) -> str:
    s = _TAG.sub(" ", s)
    s = _LINK.sub(" ", s)
    s = _LATIN.sub(" ", s)
    s = s.replace("(?)", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


_TRAILNUM = re.compile(r"[.\s|॥।,]*([0-9౦-౯]+)\s*[.|॥।]*$")


def clean_poem(p: dict, song: bool) -> dict | None:
    lines = [ln for ln in p.get("lines_telugu", []) if not _is_apparatus(ln)]
    lines = [_clean_line(ln) for ln in lines]
    lines = [ln for ln in lines if len(ln) >= 2]
    num = p.get("padyam_number")
    if lines:
        m = _TRAILNUM.search(lines[-1])
        if m:
            head = lines[-1][:m.start()].strip()
            if (num in (None, "unknown")) and m.group(1).isdigit():
                num = int(m.group(1))
            lines[-1] = head
            lines = [ln for ln in lines if ln]
    if not lines:
        return None
    if not song and len(lines) > 14:          # apparatus-dump / merged blob → drop
        return None
    p["lines_telugu"] = lines
    p["padyam_number"] = num
    return p


# ---- OCR-flag corrections (from the audit) ---------------------------------
SET_OCR = {
    "satavadhanasaramu_tirupati_venkata_kavulu",
    "kamakalanidhi_nelluri_sivaramakavi",
    "chennapuri_vilasamu_matukumalli_nrisimhakavi",
    "bhringaraja_mahimamu_dasu_sriramulu",
    "balaniti_chivukula_appayya_sastri",
}
CLEAR_OCR = {"sitaramanjaneyasamvadamu_parasuramapantula_lingamurti"}
SONG_SLUGS = {"gitanjali_adipudi_somanatharao", "gitavali_venkatadri_apparao"}


def process(slug: str) -> dict:
    fp = OUT / f"{slug}.json"
    d = json.loads(fp.read_text(encoding="utf-8"))
    song = slug in SONG_SLUGS
    before = len(d["poems"])
    cleaned = []
    for i, p in enumerate(d["poems"]):
        # drop page-anchor pseudo-chapters outright (they hold page-overlap dupes)
        if _PAGEANCHOR.match(str(p.get("chapter") or "")):
            p["chapter"] = None
        cp = clean_poem(dict(p), song)
        if cp is not None:
            cp["_pos"] = i
            cleaned.append(cp)
    # dedupe exact multi-line / substantial duplicates (page overlap), keep first
    seen, deduped = set(), []
    for p in cleaned:
        txt = "\n".join(p["lines_telugu"])
        key = txt if (len(txt) >= 40 or len(p["lines_telugu"]) >= 3) else None
        if key is not None and key in seen:
            continue
        if key is not None:
            seen.add(key)
        deduped.append(p)
    # canonical re-sequence + global id
    deduped.sort(key=lambda p: chapter_key(p.get("chapter"), p["_pos"]))
    for p in deduped:
        p.pop("_pos", None)
    out_poems = [{"id": i, **{k: v for k, v in p.items() if k != "id"}} for i, p in enumerate(deduped, 1)]
    d["poems"] = out_poems
    # flag corrections
    if slug in SET_OCR and "flag" not in d:
        d["flag"] = "OCR-sourced"
        d["note"] = "Contains OCR-garbled padyalu salvaged from an unproofread scan."
    if slug in CLEAR_OCR:
        d.pop("flag", None)
        d.pop("note", None)
    fp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"slug": slug, "before": before, "after": len(out_poems), "flag": d.get("flag")}


def main():
    slugs = sys.argv[1:]
    if not slugs:
        slugs = [b["slug"] for b in json.loads((ROOT / "crawlers" / "keep_list.json").read_text())]
    tot_b = tot_a = 0
    for s in slugs:
        r = process(s)
        tot_b += r["before"]
        tot_a += r["after"]
        d = r["before"] - r["after"]
        print(f"  {r['after']:5d}  (-{d:<4d}) {s[:44]:44s} flag={r['flag'] or '-'}")
    print(f"\nTOTAL: {tot_a} padyalu (removed {tot_b - tot_a})")


if __name__ == "__main__":
    main()
