#!/usr/bin/env python3
"""Phase 3b — build staging JSON for the 3 standalone దార్ల śatakam pages.

Despite being Word/Google-Docs pastes (each line's first akshara is a separately
coloured span), the block-aware line reader in darla_structure rejoins them into
clean blank-line-separated 4-line verses, each ending with the śatakam's makuṭam
(refrain) and a "(N)" verse number.  We strip "(N)" into padyam_number, skip the
title / "(author)" lines, and — for కవుల ధన్య చరిత — carry the poet-name colon
headings ("నన్నయ భట్టు:") as each verse's chapter (the subject poet).

Meter is NOT declared on the pages → Chandassu = unknown (user policy).
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import darla_structure as ds  # noqa: E402

PAGES = Path(__file__).resolve().parent / "darla_raw" / "pages"
OUT_DIR = Path(__file__).resolve().parent / "darla_json"

WORKS = {
    "sisuvu_satakamu": {
        "title": "శిశువు శతకము", "out": "darla_sisuvu_satakamu.json",
        "url": "https://vrdarla.blogspot.com/p/blog-page_15.html",
        "skip_titles": {"శిశువు శతకము"}, "makutam": "చిత్రమౌర",
    },
    "darla_mata_satakam": {
        "title": "దార్ల శతకము", "out": "darla_mata_satakam.json",
        "url": "https://vrdarla.blogspot.com/p/1.html",
        "skip_titles": {"దార్ల శతకము", "దార్ల మాట శతకం", "దార్ల మాట"}, "makutam": "దార్లమాట",
    },
    "kavula_dhanya_charita_satakam": {
        "title": "తెలుగు కవుల ధన్య చరిత శతకం", "out": "darla_kavula_dhanya_charita_satakam.json",
        "url": "https://vrdarla.blogspot.com/p/2.html",
        "skip_titles": {"తెలుగు కవుల ధన్య చరిత శతకం", "కవుల ధన్య చరిత శతకం"},
        "makutam": "ధన్యచరిత",
    },
}

_VNUM = re.compile(r"\s*[(\[]\s*(\d+)\s*[)\]]\s*$")     # trailing "(12)" verse number
_TITLE_RE = re.compile(r"శతక(ము|ం)")                    # mid-text title dividers
_NFC = lambda s: unicodedata.normalize("NFC", s or "")


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", _NFC(s).replace("​", ""))


def parse_satakam(body_html: str, title: str, skip_titles: set[str], makutam: str):
    """Makuṭam-driven split: every verse ends with the refrain, so we delimit on
    the refrain line (robust to both missing AND stray blank lines that the
    blank-line grouping would mis-split). Blank lines are ignored entirely."""
    lines = ds.html_to_lines(body_html)
    skip_norm = {_norm(t) for t in skip_titles} | {_norm(title)}
    verses = []            # (lines, padyam_number, chapter)
    cur: list[str] = []
    chapter: str | None = None
    pending_num = None

    def flush():
        nonlocal pending_num
        if cur:
            verses.append((list(cur), pending_num, chapter))
        cur.clear()
        pending_num = None

    for ln in lines:
        if ln == "":
            continue
        if _norm(ln) in skip_norm:                       # śatakam title line
            continue
        if _TITLE_RE.search(ln) and len(ln) <= 22:       # "శిశువు శతకం 2026" divider
            continue
        if ln.startswith(("(", "[", "（")):               # "(author)" / notes
            continue
        # poet-name colon heading ("నన్నయ భట్టు:") — sets the subject, not a line
        if ln.endswith(":") and len(ln) <= 45 and len(ln.split()) <= 6:
            chapter = ln.rstrip(":").strip()
            continue
        m = _VNUM.search(ln)
        if m:
            pending_num = int(m.group(1))
            ln = _VNUM.sub("", ln).strip()
        if ln:
            cur.append(ln)
        if makutam in _norm(ln):                          # refrain → verse end
            flush()
    flush()
    return verses


def build_one(slug: str, cfg: dict) -> dict:
    body = (PAGES / f"{slug}.html").read_text()
    verses = parse_satakam(body, cfg["title"], cfg["skip_titles"], cfg["makutam"])
    # the blog pages paste some verse-blocks twice — keep first, preserve order
    seen: set[str] = set()
    deduped = []
    for v in verses:
        k = _norm("".join(v[0]))
        if k in seen:
            continue
        seen.add(k)
        deduped.append(v)
    dropped = len(verses) - len(deduped)
    verses = deduped
    poems = []
    for i, (vlines, num, chapter) in enumerate(verses, 1):
        rec = {
            "id": i,
            "padyam_number": num if num is not None else i,
            "lines_telugu": vlines,
            "Chandassu": "unknown",
            "bhavam": None,
            "prathipadartham": None,
        }
        if chapter:
            rec["chapter"] = chapter
        if not (3 <= len(vlines) <= 8):
            rec["flag"] = f"line-count={len(vlines)} review"
        poems.append(rec)
    rec = {
        "shatakam_title_telugu": cfg["title"],
        "author_telugu": "దార్ల వెంకటేశ్వరరావు",
        "year": "2018–2026",
        "literary_form_telugu": "శతకము",
        "source_url": cfg["url"],
        "flag": "vrdarla.blogspot.com (దార్ల వెంకటేశ్వరరావు, contemporary śatakam)",
        "poems": poems,
        "_dropped": dropped,
    }
    return rec


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    from collections import Counter
    for slug, cfg in WORKS.items():
        rec = build_one(slug, cfg)
        dropped = rec.pop("_dropped")
        rec["_dropped"] = dropped   # keep for the print line below
        fp = OUT_DIR / cfg["out"]
        to_write = {k: v for k, v in rec.items() if k != "_dropped"}
        fp.write_text(json.dumps(to_write, ensure_ascii=False, indent=1), encoding="utf-8")
        lc = Counter(len(p["lines_telugu"]) for p in rec["poems"])
        flagged = [p for p in rec["poems"] if p.get("flag")]
        chaps = sorted({p["chapter"] for p in rec["poems"] if p.get("chapter")})
        print(f"{cfg['out']}: {len(rec['poems'])} verses | line-counts={dict(sorted(lc.items()))}"
              f" | flagged={len(flagged)} | chapters={len(chaps)} | src-dupes dropped={rec['_dropped']}")


if __name__ == "__main__":
    main()
