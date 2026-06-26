#!/usr/bin/env python3
"""Crawl the శతకసాహిత్యం blog (shatakashityam.blogspot.com) — save the raw body
of every post whose title contains శతకము/శతకం (a full śatakam each) to
crawlers/shatakashityam_raw/NN_<slug>.json. Index-prefixed filenames guarantee
uniqueness. Index/intro posts (శతకాల పట్టిక/పరిచయం) are skipped."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

import requests

BLOG = "https://shatakashityam.blogspot.com"
OUT = Path(__file__).resolve().parent / "shatakashityam_raw"


def _clean(b: str) -> str:
    t = re.sub(r"<br\s*/?>", "\n", b)
    t = re.sub(r"</?(div|p)[^>]*>", "\n", t)
    t = re.sub(r"<[^>]+>", "", t)
    return html.unescape(t)


def all_posts(s: requests.Session) -> list[dict]:
    posts, seen, pmax = [], set(), None
    while True:
        p = {"alt": "json", "max-results": 150, "orderby": "published"}
        if pmax:
            p["published-max"] = pmax
        ents = s.get(f"{BLOG}/feeds/posts/default", params=p, timeout=30).json()["feed"].get("entry", [])
        if not ents:
            break
        new = 0
        for e in ents:
            if e["id"]["$t"] in seen:
                continue
            seen.add(e["id"]["$t"])
            posts.append(e)
            new += 1
        if new == 0:
            break
        pmax = min(e["published"]["$t"] for e in ents)
    return posts


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0 (padyarchana research crawler)"
    posts = all_posts(s)
    shatak = [e for e in posts if ("శతకము" in e["title"]["$t"] or "శతకం" in e["title"]["$t"])]
    manifest = []
    for i, e in enumerate(shatak):
        labels = [c["term"] for c in e.get("category", [])]
        body = e.get("content", {}).get("$t", "") or e.get("summary", {}).get("$t", "")
        en = next((l for l in labels if l.isascii() and len(l) > 3 and l != "SatakasAhityaM"), None)
        slug = re.sub(r"[^a-z0-9]+", "_", (en or "shatakam").lower()).strip("_")
        rec = {
            "title": e["title"]["$t"], "labels": labels,
            "url": next((l["href"] for l in e["link"] if l["rel"] == "alternate"), None),
            "published": e["published"]["$t"][:10], "body_text": _clean(body),
        }
        (OUT / f"{i:02d}_{slug}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        manifest.append({k: v for k, v in rec.items() if k != "body_text"})
    json.dump(manifest, open(OUT / "manifest.json", "w"), ensure_ascii=False, indent=1)
    print(f"total posts: {len(posts)} | śatakam posts saved: {len(shatak)}")
    print(f"skipped (non-śatakam): {len(posts) - len(shatak)}")


if __name__ == "__main__":
    main()
