#!/usr/bin/env python3
"""Phase 3a — build the staging JSON for the దార్ల blog day-posts.

Produces crawlers/darla_json/darla_blog_padyalu.json (padyarchana import shape)
plus a human-readable review report.  Author = దార్ల వెంకటేశ్వరరావు for all
(user decision); the few posts that are someone else's padyam carry a per-poem
`note` + `original_author`.  Provenance (source_url, published, post title as
chapter) and extraction `flag`s (auto-split-4 / short-review) are kept so the
review can target exactly the uncertain entries.  The 3 standalone śatakam pages
are built separately (darla_build_satakams.py).
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import darla_structure as ds  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent / "darla_json"
SOURCE = "దార్ల వెంకటేశ్వరరావు పద్యాలు (బ్లాగు)"
BLOG = "https://vrdarla.blogspot.com"

# Per-post overrides keyed by feed index. note → per-poem provenance note;
# original_author → the actual author when not దార్ల; keep → restrict to these
# padyam positions (0-based) within the post.
OVERRIDES: dict[int, dict] = {
    38: {"original_author": "దార్ల శ్రీనివాసరావు",
         "note": "తొలి పద్యం — దార్ల శ్రీనివాసరావు (బాబు; దార్ల వెంకటేశ్వరరావు కుమారుడు) రచన",
         "keep": [0]},
    81: {"original_author": "డా. జె.వి.చలపతిరావు",
         "note": "రచన: కవికోకిల డా. జె.వి.చలపతిరావు (దార్ల వెంకటేశ్వరరావును ప్రశంసిస్తూ)"},
    77: {"note": "'చలపతిరావు' లేబుల్‌తో పోస్ట్; రచయిత ధృవీకరించాలి"},
}


def clean_chapter(title: str) -> str:
    t = unicodedata.normalize("NFC", title or "").replace("​", "").strip()
    return re.sub(r"\s+", " ", t)


def norm_key(lines: list[str]) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", "".join(lines)))


def build() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    posts = ds.load_posts()
    poems: list[dict] = []
    report: list[str] = []
    seen: set[str] = set()
    # seed with śatakam verses so blog reprints (the 2018 గణేష్-పత్రిక posts that
    # republished దార్ల మాట శతకం) collapse into the canonical śatakam files
    sat_dupes = 0
    for sf in OUT_DIR.glob("darla_*_satakam*.json"):
        for p in json.loads(sf.read_text()).get("poems", []):
            seen.add(norm_key(p["lines_telugu"]))
    seeded = len(seen)
    dup = 0
    pid = 0
    for d in posts:
        idx = d["idx"]
        ov = OVERRIDES.get(idx, {})
        pad, _ = ds.parse_post(d["body_html"], d["title"])
        flat: list[ds.Padyam] = []
        for p in pad:
            flat.extend(ds.split_fused(p))
        good = [p for p in flat if ds.confident(p)]
        if "keep" in ov:
            good = [p for i, p in enumerate(good) if i in set(ov["keep"])]
        # user policy: keep ONLY four-line padyalu (drop fragments, prose tails,
        # and longer meters like 8-line సీసపద్యాలు)
        good = [p for p in good if len(p.lines) == 4]
        kept = 0
        for pos, p in enumerate(good, 1):
            key = norm_key(p.lines)
            if key in seen:
                dup += 1
                continue
            seen.add(key)
            pid += 1
            flag = p.flag
            if len(p.lines) in (2, 3) and not flag:
                flag = "short-review"
            rec = {
                "id": pid,
                "padyam_number": pos,
                "lines_telugu": p.lines,
                "Chandassu": p.meter or "unknown",
                "chapter": clean_chapter(d["title"]),
                "bhavam": "\n".join(p.bhavam) if p.bhavam else None,
                "prathipadartham": None,
                "source_url": d["url"],
                "published": d["published"][:10],
            }
            if ov.get("original_author"):
                rec["original_author"] = ov["original_author"]
                # surface the real author in the (DB-visible) title; poet stays దార్ల
                rec["title"] = (f"{SOURCE} - {clean_chapter(d['title'])} - c{pid}"
                                f" · రచన: {ov['original_author']}")
            if ov.get("note"):
                rec["note"] = ov["note"]
            if flag:
                rec["flag"] = flag
            poems.append(rec)
            kept += 1
        tag = ""
        if idx in OVERRIDES:
            tag = "  [override]"
        if kept == 0:
            tag = "  <-- 0 padyalu (prose/diary/image-only)"
        report.append(f"  #{idx:2d} {kept:3d}  {d['title'][:54]}{tag}")

    rec = {
        "shatakam_title_telugu": SOURCE,
        "author_telugu": "దార్ల వెంకటేశ్వరరావు",
        "year": "2018–2026",
        "literary_form_telugu": "online padyalu",
        "source_url": BLOG,
        "flag": "online-padyalu; vrdarla.blogspot.com (దార్ల వెంకటేశ్వరరావు, contemporary)",
        "note": ("Topical పద్యాలు (mostly 4-line ఆటవెలది/తేటగీతి) crawled from "
                 "vrdarla.blogspot.com under the పద్యాలు label. Meter = poet-declared "
                 "where given, else unknown. bhavam captured where the post explained it. "
                 "Each poem's `chapter` is its source post; `flag` marks entries to review."),
        "poems": poems,
    }
    fp = OUT_DIR / "darla_blog_padyalu.json"
    fp.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")

    from collections import Counter
    meters = Counter(p["Chandassu"] for p in poems)
    flags = Counter(p.get("flag") for p in poems if p.get("flag"))
    bhav = sum(1 for p in poems if p["bhavam"])
    print("\n".join(report))
    print(f"\n=== {fp.name}: {len(poems)} padyalu "
          f"({dup} exact-dupes dropped, incl. śatakam reprints; "
          f"{seeded} śatakam keys seeded) | bhavam={bhav} ===")
    print("meters:", dict(meters))
    print("flags to review:", dict(flags))


if __name__ == "__main__":
    build()
