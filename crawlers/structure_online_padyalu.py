#!/usr/bin/env python3
"""Structure the extracted శంకరాభరణం blog padyalu into padyarchana-format JSON,
split by challenge-type, into a staging folder for human verification before any
onboarding.

  * author_telugu      = "unknown"           (per user: blog contributors are not DB poets)
  * literary_form      = "online padyalu"     (the ad-hoc category)
  * Chandassu          = poet-declared meter when present, else "unknown"
  * per-poem provenance: commenter, challenge, challenge_type, date, source_url
                         (kept so nothing is lost; poet stays "unknown")

Exact duplicates (identical lines AND same commenter — re-posts/corrections) are
collapsed.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "crawlers" / "shankarabharanam_extracted.json"
OUT = ROOT / "crawlers" / "online_padyalu"
BLOG = "https://kandishankaraiah.blogspot.com/"

# challenge-type → output slug
SLUG = {
    "సమస్యాపూరణం": "samasyapuranam", "సమస్యాపూరణ": "samasyapuranam",
    "పద్య రచన": "padyaracana", "దత్తపది": "dattapadi", "న్యస్తాక్షరి": "nyastakshari",
    "నిషిద్ధాక్షరి": "nishiddhakshari", "అవీ - ఇవీ": "avi_ivi",
    "చమత్కార పద్యాలు": "chamatkara", "విశేషచ్ఛందస్సులు": "visesha_chandassu",
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    P = json.loads(SRC.read_text())
    # collapse exact re-posts (same lines + same commenter)
    seen: set = set()
    buckets: dict[str, list] = defaultdict(list)
    dupes = 0
    for p in P:
        key = (tuple(p["lines_telugu"]), p["poet"])
        if key in seen:
            dupes += 1
            continue
        seen.add(key)
        ctype = p["challenge_type"] or "ఇతర"
        slug = SLUG.get(ctype, "itara")
        buckets[slug].append((ctype, p))

    summary = []
    for slug, items in sorted(buckets.items(), key=lambda x: -len(x[1])):
        ctypes = sorted({c for c, _ in items})
        poems = []
        for i, (ctype, p) in enumerate(items, 1):
            commenter = p["poet"].strip() or "unknown"
            poems.append({
                "id": i,
                "lines_telugu": p["lines_telugu"],
                "Chandassu": p["Chandassu"],
                "title": f"{p['challenge']} — {commenter}",
                "chapter": ctype,
                "commenter": commenter,
                "challenge": p["challenge"],
                "published": p["published"],
                "source_url": p["source_url"],
                "bhavam": None,
                "prathipadartham": None,
            })
        rec = {
            "shatakam_title_telugu": f"శంకరాభరణం — ఆన్‌లైన్ పద్యాలు ({'/'.join(ctypes)})",
            "author_telugu": "unknown",
            "year": "2008–2026",
            "literary_form_telugu": "online padyalu",
            "source_url": BLOG,
            "flag": "online-padyalu",
            "note": ("Ad-hoc padyalu crawled from the శంకరాభరణం blog comments (కంది శంకరయ్య). "
                     "Poet = unknown; original commenter kept per-poem as provenance. "
                     "Precision-first extraction, ~95% clean (sample-estimated); held for verification."),
            "poems": poems,
        }
        fp = OUT / f"online_padyalu_{slug}.json"
        fp.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        mb = fp.stat().st_size / 1e6
        summary.append((slug, len(poems), ctypes, mb))

    print(f"source padyalu: {len(P)} | after exact-dedup: {len(seen)} (removed {dupes} re-posts)\n")
    print(f"{'file':40s} {'poems':>7s} {'MB':>6s}  challenge-types")
    tot = 0
    for slug, n, ctypes, mb in summary:
        tot += n
        print(f"online_padyalu_{slug}.json{'':<14} {n:7d} {mb:6.1f}  {', '.join(ctypes)[:40]}")
    print(f"\nTOTAL structured: {tot} padyalu across {len(summary)} files in {OUT}")


if __name__ == "__main__":
    main()
