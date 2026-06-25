#!/usr/bin/env python3
"""Phase 1 — raw crawl of the శంకరాభరణం blog (kandishankaraiah.blogspot.com).

A సమస్యాపూరణం/అవధానం blog: each post is a challenge (సమస్య/దత్తపది/వర్ణన…) and the
padyalu live in the COMMENTS (by many different poets), occasionally in the post
body too. We pull everything via Blogger's JSON feeds (robust, paginated) — NOT
HTML scraping — and dump one JSON file per post (post metadata + content + every
comment) into a folder. Resumable: existing post files are skipped.

  posts feed   : /feeds/posts/default?alt=json&max-results=N&start-index=K
  comment feed : /feeds/<postId>/comments/default?alt=json&...

Phase 2 (analysis/extraction) is a separate step over the dumped folder.
"""
from __future__ import annotations

import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

BLOG = "https://kandishankaraiah.blogspot.com"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "crawlers" / "shankarabharanam_raw"
POSTS_DIR = OUT / "posts"
MANIFEST = OUT / "manifest.json"

_TL = __import__("threading").local()
_last = [0.0]
_lock = __import__("threading").Lock()
MIN_INTERVAL = 0.34


def _session() -> requests.Session:
    s = getattr(_TL, "s", None)
    if s is None:
        s = requests.Session()
        s.headers["User-Agent"] = "Mozilla/5.0 (padyarchana research crawler; contact samvaran)"
        _TL.s = s
    return s


def _throttle():
    with _lock:
        dt = time.time() - _last[0]
        if dt < MIN_INTERVAL:
            time.sleep(MIN_INTERVAL - dt)
        _last[0] = time.time()


def feed(path: str, params: dict) -> dict | None:
    url = f"{BLOG}{path}"
    for attempt in range(6):
        try:
            _throttle()
            r = _session().get(url, params=params, timeout=45)
            if r.status_code in (429, 503, 500):
                time.sleep(min(60, 4 * 2 ** attempt))
                continue
            r.raise_for_status()
            return r.json()
        except Exception:
            time.sleep(2 * (attempt + 1))
    return None


def _post_id(entry: dict) -> str:
    m = re.search(r"post-(\d+)", entry["id"]["$t"])
    return m.group(1) if m else entry["id"]["$t"]


def _alt(links: list) -> str | None:
    return next((l["href"] for l in links if l.get("rel") == "alternate"), None)


def extract_post(e: dict) -> dict:
    return {
        "postId": _post_id(e),
        "title": e.get("title", {}).get("$t", ""),
        "published": e.get("published", {}).get("$t", ""),
        "updated": e.get("updated", {}).get("$t", ""),
        "url": _alt(e.get("link", [])),
        "labels": [c["term"] for c in e.get("category", [])],
        "comment_count": int(e.get("thr$total", {}).get("$t", 0) or 0),
        "content_html": e.get("content", {}).get("$t", "") or e.get("summary", {}).get("$t", ""),
    }


def extract_comment(c: dict) -> dict:
    a = (c.get("author") or [{}])[0]
    return {
        "id": _post_id(c),
        "author": a.get("name", {}).get("$t", ""),
        "author_uri": a.get("uri", {}).get("$t", ""),
        "published": c.get("published", {}).get("$t", ""),
        "content_html": c.get("content", {}).get("$t", "") or c.get("summary", {}).get("$t", ""),
    }


def all_posts() -> list[dict]:
    """Date-windowed pagination: Blogger's start-index paging returns short
    pages mid-stream (not a reliable end signal), so we walk backwards by
    `published-max`, deduping the inclusive boundary post each window."""
    posts: list[dict] = []
    seen: set[str] = set()
    pmax: str | None = None
    while True:
        params = {"alt": "json", "max-results": 150, "orderby": "published"}
        if pmax:
            params["published-max"] = pmax
        d = feed("/feeds/posts/default", params)
        entries = (d or {}).get("feed", {}).get("entry", []) if d else []
        if not entries:
            break
        new = 0
        for e in entries:
            p = extract_post(e)
            if p["postId"] in seen:
                continue
            seen.add(p["postId"])
            posts.append(p)
            new += 1
        oldest = min(e["published"]["$t"] for e in entries)
        print(f"  posts: {len(posts)} (+{new}, window <= {oldest[:10]})", flush=True)
        if new == 0:                      # window produced nothing new → done
            break
        pmax = oldest
    return posts


def fetch_comments(post_id: str) -> list[dict]:
    out: list[dict] = []
    start, step = 1, 200
    while True:
        d = feed(f"/feeds/{post_id}/comments/default", {"alt": "json", "max-results": step, "start-index": start})
        entries = (d or {}).get("feed", {}).get("entry", []) if d else []
        if not entries:
            break
        out.extend(extract_comment(c) for c in entries)
        if len(entries) < step:
            break
        start += step
    return out


def crawl_one(args) -> tuple[str, int]:
    seq, post = args
    fp = POSTS_DIR / f"{post['postId']}.json"
    if fp.exists():
        return post["postId"], -1   # already done (resume)
    comments = fetch_comments(post["postId"]) if post["comment_count"] else []
    rec = {**post, "seq": seq, "comments": comments}
    fp.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    return post["postId"], len(comments)


def main():
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    if MANIFEST.exists():
        posts = json.loads(MANIFEST.read_text())
        print(f"manifest exists: {len(posts)} posts", flush=True)
    else:
        print("fetching all post metadata…", flush=True)
        posts = all_posts()
        for i, p in enumerate(posts, 1):
            p["seq"] = i
        MANIFEST.write_text(json.dumps(posts, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"manifest written: {len(posts)} posts", flush=True)

    todo = [(p["seq"], p) for p in posts]
    done = sum(1 for p in posts if (POSTS_DIR / f"{p['postId']}.json").exists())
    print(f"already crawled: {done}/{len(posts)}; crawling the rest with comments…", flush=True)
    n = 0
    total_c = 0
    with ThreadPoolExecutor(max_workers=4) as ex:
        for pid, nc in ex.map(crawl_one, todo):
            n += 1
            if nc >= 0:
                total_c += nc
            if n % 200 == 0:
                print(f"  {n}/{len(todo)} posts processed, ~{total_c} comments saved", flush=True)
    files = len(list(POSTS_DIR.glob("*.json")))
    print(f"\nDONE: {files} post files in {POSTS_DIR}", flush=True)


if __name__ == "__main__":
    main()
