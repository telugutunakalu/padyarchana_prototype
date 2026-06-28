#!/usr/bin/env python3
"""Phase 1 — raw crawl of దార్ల వెంకటేశ్వరరావు's blog (vrdarla.blogspot.com).

A personal Telugu-poetry blog. The padyalu live in the POST BODY (mostly topical
4-line ఆటవెలది/తేటగీతి written for a day-of-observance), not in comments. We
enumerate every post under the పద్యాలు label via Blogger's JSON feed (robust,
paginated), then fetch each post's *rendered HTML* — the feed's `content` field
strips the per-line `<p>`/`<br>` block tags, destroying line structure, so the
rendered page is the only reliable source. The post-body div is saved verbatim.

We also grab three standalone Blogger *pages* (/p/…) that hold full śatakams
(శిశువు శతకము, దార్ల మాట శతకం, తెలుగు కవుల ధన్య చరిత శతకం); these are messy
Word/Google-Docs pastes handled by per-page parsers in the structurer.

Resumable: existing post/page files are skipped. Phase 2 (structuring) is
crawlers/darla_structure.py over this dump.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import requests

BLOG = "https://vrdarla.blogspot.com"
LABEL = "పద్యాలు"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "crawlers" / "darla_raw"
POSTS_DIR = OUT / "posts"
MANIFEST = OUT / "manifest.json"

# Standalone śatakam pages the user pointed out (Blogger "pages", not posts —
# they never appear in the posts feed).
PAGES = {
    "sisuvu_satakamu": "https://vrdarla.blogspot.com/p/blog-page_15.html",
    "darla_mata_satakam": "https://vrdarla.blogspot.com/p/1.html",
    "kavula_dhanya_charita_satakam": "https://vrdarla.blogspot.com/p/2.html",
}

MIN_INTERVAL = 0.34
_last = [0.0]


def _session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0 (padyarchana research crawler; contact samvaran)"
    return s


SESS = _session()


def _throttle():
    dt = time.time() - _last[0]
    if dt < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - dt)
    _last[0] = time.time()


def get(url: str, params: dict | None = None) -> requests.Response | None:
    for attempt in range(6):
        try:
            _throttle()
            r = SESS.get(url, params=params, timeout=45)
            if r.status_code in (429, 503, 500):
                time.sleep(min(60, 4 * 2 ** attempt))
                continue
            r.raise_for_status()
            return r
        except Exception:
            time.sleep(2 * (attempt + 1))
    return None


def _post_id(entry: dict) -> str:
    m = re.search(r"post-(\d+)", entry["id"]["$t"])
    return m.group(1) if m else entry["id"]["$t"]


def _alt(links: list) -> str | None:
    return next((l["href"] for l in links if l.get("rel") == "alternate"), None)


def enumerate_posts() -> list[dict]:
    """All posts under the పద్యాలు label, via start-index paging on the
    label feed (small enough — ~91 — that simple paging is reliable)."""
    posts: list[dict] = []
    seen: set[str] = set()
    start, step = 1, 25
    while True:
        r = get(f"{BLOG}/feeds/posts/default/-/{LABEL}",
                {"alt": "json", "max-results": step, "start-index": start})
        entries = (r.json()["feed"].get("entry", []) if r else [])
        if not entries:
            break
        for e in entries:
            pid = _post_id(e)
            if pid in seen:
                continue
            seen.add(pid)
            posts.append({
                "postId": pid,
                "title": e.get("title", {}).get("$t", ""),
                "published": e.get("published", {}).get("$t", ""),
                "updated": e.get("updated", {}).get("$t", ""),
                "url": _alt(e.get("link", [])),
                "labels": [c["term"] for c in e.get("category", [])],
                "comment_count": int(e.get("thr$total", {}).get("$t", 0) or 0),
            })
        if len(entries) < step:
            break
        start += step
    return posts


_BODY_RE = re.compile(
    r'<div class=["\']post-body[^>]*>(.*?)<div class=["\']post-footer', re.S)
_BODY_FALLBACK = re.compile(
    r'<div class=["\']post-body[^>]*>(.*?)</div>\s*</div>', re.S)


def extract_post_body(html: str) -> str:
    m = _BODY_RE.search(html) or _BODY_FALLBACK.search(html)
    return m.group(1).strip() if m else ""


def crawl_posts(posts: list[dict]) -> None:
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    done = new = 0
    for p in posts:
        fp = POSTS_DIR / f"{p['postId']}.json"
        if fp.exists():
            done += 1
            continue
        r = get(p["url"])
        body = extract_post_body(r.text) if r else ""
        rec = {**p, "body_html": body, "has_image": "<img" in body}
        fp.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        new += 1
        if new % 20 == 0:
            print(f"  …{new} new posts fetched", flush=True)
    print(f"posts: {done} already on disk, {new} newly fetched "
          f"({len(list(POSTS_DIR.glob('*.json')))} total)", flush=True)


def crawl_pages() -> None:
    pdir = OUT / "pages"
    pdir.mkdir(parents=True, exist_ok=True)
    for slug, url in PAGES.items():
        fp = pdir / f"{slug}.html"
        if fp.exists():
            print(f"  page {slug}: already on disk")
            continue
        r = get(url)
        body = extract_post_body(r.text) if r else ""
        fp.write_text(body, encoding="utf-8")
        print(f"  page {slug}: {len(body)} chars body  <- {url}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if MANIFEST.exists():
        posts = json.loads(MANIFEST.read_text())
        print(f"manifest exists: {len(posts)} posts", flush=True)
    else:
        print(f"enumerating posts under label '{LABEL}'…", flush=True)
        posts = enumerate_posts()
        MANIFEST.write_text(json.dumps(posts, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"manifest written: {len(posts)} posts", flush=True)
    crawl_posts(posts)
    print("\nfetching standalone śatakam pages…", flush=True)
    crawl_pages()
    print("\nDONE.", flush=True)


if __name__ == "__main__":
    main()
