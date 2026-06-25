#!/usr/bin/env python3
"""Structure అభాగ్యోపాఖ్యానము (కందుకూరి వీరేశలింగం, 1898) from Wikisource.

A హాస్య ప్రబంధము (humorous prabandha) by the great 19th-century Telugu reformer.
The Wikisource page renders the entire work on a single page with no chapter
breaks, and — unlike most kāvyas — its HTML emits all padyalu of a section on
one wrapped paragraph with no `<br>` between verses. So our cleaned text lands
as a 4 KB mega-line per section.

Fix: pre-split the body on padyam boundaries. The reliable boundary is
"<verse-number> <whitespace> <marker abbrev>." so we insert a newline at every
such junction before handing off to text_to_json.parse_padyalu.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wikisource_crawler as w  # noqa: E402
import text_to_json as t  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "padyalu_json_data"
WORK = "అభాగ్యోపాఖ్యానము"

# Markers ordered longest-first so multi-char abbreviations win over their prefixes
# (e.g. "శ్లో" must beat "శా"). Matches text_to_json.MARKERS keys.
_MARK_ALT = "|".join(sorted(t.MARKERS, key=len, reverse=True))

# Split point: a digit run (Telugu \d also matches Telugu numerals) followed by
# whitespace and a known meter marker. The lookbehind anchors us to the verse-
# number ending the previous padyam; the lookahead anchors us to the next padyam's
# opening marker.
_SPLIT_RE = re.compile(rf"(?<=\d)\s+(?=(?:{_MARK_ALT})\.\s)")


def main() -> None:
    txt = w.fetch_rendered(WORK)
    # Skip the colophon / title block at the top — the actual padyalu begin at
    # the second occurrence of the work title (the first is the page heading).
    first = txt.find(WORK)
    second = txt.find(WORK, first + 1) if first != -1 else -1
    body = txt[second:] if second != -1 else txt

    # Inject padyam-boundary newlines so each verse lives on its own line.
    body = _SPLIT_RE.sub("\n", body)

    poems = t.parse_padyalu(body)
    poems = [{"id": i, **{k: v for k, v in p.items() if k != "id"}}
             for i, p in enumerate(poems, 1)]

    rec = {
        "shatakam_title_telugu": WORK,
        "author_telugu": "కందుకూరి వీరేశలింగం",
        "year": 1898,
        "literary_form_telugu": "హాస్య ప్రబంధము",
        "source_url": "https://te.wikisource.org/wiki/" + WORK,
        "poems": poems,
    }

    OUT.mkdir(exist_ok=True)
    fp_out = OUT / "abhagyopakhyanamu_kandukuri_veereshalingam.json"
    fp_out.write_text(
        json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    from collections import Counter
    meters = Counter(p["Chandassu"] for p in poems)
    nums = [p["padyam_number"] for p in poems if isinstance(p["padyam_number"], int)]
    print(f"\n-> {fp_out.name} ({len(poems)} padyalu)")
    print(f"   verse-number range: {min(nums)}…{max(nums)}")
    print(f"   meters: " + ", ".join(f"{k}={v}" for k, v in meters.most_common()))


if __name__ == "__main__":
    main()
