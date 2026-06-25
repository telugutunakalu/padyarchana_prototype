#!/usr/bin/env python3
"""Crawl Telugu Wikisource kavyas (kāvyaṃ) into plain-text files.

Two source shapes are supported:

1. A "transcluded work": a main page whose chapter sub-pages (ఆశ్వాసములు) each
   transclude a range of proofread Page: (పుట:) pages via <pages .../>.
   Fetching the *rendered* HTML of a chapter page assembles the whole chapter,
   so we crawl one file per chapter plus a combined file.

2. A "page range": a Page: (పుట:) namespace document where the caller gives an
   explicit /from../to range. Each proofread page is fetched and concatenated.

Text is obtained from the MediaWiki parse API (prop=text) so that all templates
({{c|N}} verse numbers, {{float right|N}} line numbers, poem line breaks, …) are
expanded exactly as they read on the site, then converted to clean text with a
stdlib HTML parser (no bs4 dependency). Running headers, page-quality banners,
edit links and inline ref markers are dropped; per-page footnotes are preserved
under a small heading so no editorial text is lost.

Run:  ./venv/bin/python crawlers/wikisource_crawler.py
"""
from __future__ import annotations

import html
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path

import requests

API = "https://te.wikisource.org/w/api.php"
OUT_DIR = Path(__file__).resolve().parent
UA = "padyarchana-crawler/1.0 (samvaran.kashyap@gmail.com)"

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA})

# one Session per worker thread for safe connection reuse during parallel crawls
_TL = threading.local()

# global throttle: at most one request every MIN_INTERVAL seconds, across all
# threads, to stay well under Wikimedia's rate limits (avoids HTTP 429).
MIN_INTERVAL = 0.6
_throttle_lock = threading.Lock()
_last_request = [0.0]


def _throttle() -> None:
    with _throttle_lock:
        now = time.monotonic()
        wait = MIN_INTERVAL - (now - _last_request[0])
        if wait > 0:
            time.sleep(wait)
        _last_request[0] = time.monotonic()


def _session() -> requests.Session:
    s = getattr(_TL, "session", None)
    if s is None:
        s = requests.Session()
        s.headers.update({"User-Agent": UA})
        _TL.session = s
    return s

# class tokens whose whole subtree should be dropped from the text
_SKIP_CLASSES = {
    "prp-page-qualityheader",   # "ఈ పుట అచ్చుదిద్దబడ్డది" banner
    "wst-running-header",       # printed running head (page numbers + title)
    "mw-cite-backlink",         # the "↑" backlinks in the footnote list
    "cite-bracket",             # the [ ] around inline ref numbers
    "reference",                # inline superscript ref marker, e.g. [1]
    "mw-editsection",           # "[edit]" links
    "noprint",
}
_SKIP_TAGS = {"style", "script"}
_BLOCK_TAGS = {"p", "div", "li", "tr", "ol", "ul", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote"}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._out: list[str] = []
        self._skip_depth = 0
        # stack of (tag, contributes_to_skip) so we can unwind on endtag
        self._stack: list[tuple[str, bool]] = []

    def handle_starttag(self, tag, attrs):
        if tag == "br":
            if not self._skip_depth:
                self._out.append("\n")
            return
        attrd = dict(attrs)
        classes = set((attrd.get("class") or "").split())
        is_skip = tag in _SKIP_TAGS or bool(classes & _SKIP_CLASSES)
        # <link>, <img>, <br> are void; HTMLParser still calls starttag for some,
        # but we only push tags that get a matching endtag.
        if tag in ("link", "img", "br", "hr", "meta", "input"):
            return
        self._stack.append((tag, is_skip))
        if is_skip:
            self._skip_depth += 1

    def handle_startendtag(self, tag, attrs):
        # self-closing tags like <br/>, <link/>
        if tag == "br" and not self._skip_depth:
            self._out.append("\n")

    def handle_endtag(self, tag):
        # unwind the stack to the matching tag
        for i in range(len(self._stack) - 1, -1, -1):
            t, is_skip = self._stack[i]
            if t == tag:
                if is_skip:
                    self._skip_depth -= 1
                del self._stack[i:]
                break
        if tag in _BLOCK_TAGS and not self._skip_depth:
            self._out.append("\n")

    def handle_data(self, data):
        if not self._skip_depth:
            # text-node whitespace (incl. source newlines & &#160; indents) is
            # not structurally meaningful in HTML — collapse to a single space.
            # Real line breaks come only from <br> and block-tag boundaries.
            self._out.append(re.sub(r"\s+", " ", data))

    def text(self) -> str:
        return "".join(self._out)


def _clean(raw_html: str) -> str:
    p = _TextExtractor()
    p.feed(raw_html)
    txt = p.text()
    txt = txt.replace("\xa0", " ")
    # strip zero-width / joiner artifacts left by float-right number templates
    txt = re.sub(r"[​‌‍⁠﻿]", "", txt)
    txt = html.unescape(txt)
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in txt.split("\n")]
    out: list[str] = []
    blanks = 0
    for ln in lines:
        if ln:
            blanks = 0
            out.append(ln)
        else:
            blanks += 1
            if blanks <= 1:
                out.append("")
    return "\n".join(out).strip() + "\n"


def fetch_rendered(title: str, retries: int = 6) -> str:
    """Return cleaned plain text for a wiki page title (any namespace)."""
    params = {
        "action": "parse",
        "page": title,
        "prop": "text",
        "format": "json",
        "formatversion": 2,
        "disablelimitreport": 1,
        "disableeditsection": 1,
    }
    last = None
    for attempt in range(retries):
        try:
            _throttle()
            r = _session().get(API, params=params, timeout=60)
            if r.status_code == 429:
                # honour Retry-After; otherwise exponential backoff
                ra = r.headers.get("Retry-After")
                delay = float(ra) if (ra and ra.isdigit()) else min(60.0, 5.0 * 2 ** attempt)
                print(f"      429 on {title} — backing off {delay:.0f}s")
                time.sleep(delay)
                last = RuntimeError("429 Too Many Requests")
                continue
            r.raise_for_status()
            data = r.json()
            if "error" in data:
                # a missing/empty Page: page is not fatal — treat as blank
                info = data["error"].get("info", "API error")
                if data["error"].get("code") == "missingtitle":
                    return ""
                raise RuntimeError(info)
            return _clean(data["parse"]["text"])
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2.0 * (attempt + 1))
    raise RuntimeError(f"failed to fetch {title!r}: {last}")


def crawl_page_range_parallel(base: str, lo: int, hi: int, slug: str,
                              title_human: str, workers: int = 6,
                              skip_empty: bool = True) -> None:
    """Crawl పుట:<base>/<n> for n in [lo, hi] concurrently and concatenate in
    page order. Empty/blank proofread pages are skipped when skip_empty."""
    nums = list(range(lo, hi + 1))
    results: dict[int, str] = {}

    def work(n: int) -> tuple[int, str]:
        return n, fetch_rendered(f"పుట:{base}/{n}")

    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for n, body in ex.map(work, nums):
            results[n] = body
            done += 1
            if done % 25 == 0 or done == len(nums):
                print(f"    fetched {done}/{len(nums)} pages")

    parts: list[str] = []
    kept = 0
    for n in nums:
        body = results.get(n, "").strip()
        if skip_empty and not body:
            continue
        kept += 1
        parts.append(f"{'-'*70}\n[పుట {n}]\n{'-'*70}\n\n{body}")
    header = f"{'='*70}\n{title_human}\nపుట:{base} (pp. {lo}-{hi}; {kept} non-empty)\n{'='*70}\n\n"
    fp = OUT_DIR / f"{slug}_full.txt"
    fp.write_text(header + "\n".join(parts), encoding="utf-8")
    print(f"  -> {fp.name} ({kept}/{len(nums)} pages with content)")


def list_chapter_subpages(main_title: str) -> list[str]:
    """Return ns-0 sub-page titles linked from a work's main page, ordered."""
    r = SESSION.get(API, params={
        "action": "parse", "page": main_title, "prop": "links",
        "format": "json", "formatversion": 2,
    }, timeout=60)
    r.raise_for_status()
    links = [l["title"] for l in r.json()["parse"]["links"]
             if l.get("ns") == 0 and l["title"].startswith(main_title + "/")]
    return sorted(set(links))


def crawl_transcluded_work(main_title: str, slug: str, chapter_order: list[str]) -> None:
    """Crawl a work whose chapters live at <main>/<chapter>. chapter_order is the
    list of chapter leaf-names in reading order."""
    found = list_chapter_subpages(main_title)
    print(f"[{slug}] sub-pages found: {[t.split('/')[-1] for t in found]}")
    combined: list[str] = []
    for idx, leaf in enumerate(chapter_order, 1):
        title = f"{main_title}/{leaf}"
        print(f"  fetching ch{idx}: {leaf} ...")
        body = fetch_rendered(title)
        header = f"{'='*70}\n{slug} — {idx:02d}. {leaf}\n{title}\n{'='*70}\n\n"
        chapter_text = header + body
        fp = OUT_DIR / f"{slug}_{idx:02d}_{translit(leaf)}.txt"
        fp.write_text(chapter_text, encoding="utf-8")
        print(f"    -> {fp.name} ({len(body)} chars)")
        combined.append(chapter_text)
        time.sleep(0.8)
    comb_fp = OUT_DIR / f"{slug}_full.txt"
    comb_fp.write_text("\n\n".join(combined), encoding="utf-8")
    print(f"  -> {comb_fp.name} (combined)")


def crawl_single_page(title: str, slug: str, title_human: str) -> None:
    """Crawl one wiki page (e.g. a śatakaṃ whose verses+bhāvaṃ are transcluded
    from a Page: range) into a single text file."""
    print(f"  fetching {title} ...")
    body = fetch_rendered(title)
    header = f"{'='*70}\n{title_human}\n{title}\n{'='*70}\n\n"
    fp = OUT_DIR / f"{slug}.txt"
    fp.write_text(header + body, encoding="utf-8")
    print(f"  -> {fp.name} ({len(body)} chars)")


def crawl_page_range(base: str, lo: int, hi: int, slug: str, title_human: str) -> None:
    """Crawl పుట:<base>/<n> for n in [lo, hi] and concatenate."""
    parts: list[str] = []
    for n in range(lo, hi + 1):
        title = f"పుట:{base}/{n}"
        print(f"  fetching page {n}/{hi} ...")
        body = fetch_rendered(title)
        parts.append(f"{'-'*70}\n[పుట {n}]\n{'-'*70}\n\n{body}")
        time.sleep(0.8)
    header = f"{'='*70}\n{title_human}\nపుట:{base} (pp. {lo}-{hi})\n{'='*70}\n\n"
    comb_fp = OUT_DIR / f"{slug}_full.txt"
    comb_fp.write_text(header + "\n".join(parts), encoding="utf-8")
    print(f"  -> {comb_fp.name} ({hi - lo + 1} pages)")


_TRANSLIT = {
    "ప్రథమాశ్వాసము": "01_prathamaswasamu",
    "ద్వితీయాశ్వాసము": "02_dvitiyaswasamu",
    "తృతీయాశ్వాసము": "03_trutiyaswasamu",
    "చతుర్థాశ్వాసము": "04_chaturthaswasamu",
    "పంచమాశ్వాసము": "05_panchamaswasamu",
    "షష్ఠాశ్వాసము": "06_shashthaswasamu",
    # గోపీనాథ రామాయణము kāṇḍas + author preface
    "గోపీనాథ రామాయణము - పీఠిక": "00_pithika",
    "బాలకాండము": "01_balakandamu",
    "అయోధ్యాకాండము": "02_ayodhyakandamu",
    "అయోధ్యాకాండము (కొనసాగింపు)": "03_ayodhyakandamu_contd",
    "ఆరణ్యకాండము": "04_aranyakandamu",
    # శ్రీ ప్రబంధరాజ … విజయ విలాసము sections
    "పాఠము": "01_avatarika",
    "ఏకాశ్వాసము": "02_ekaswasamu",
}


def translit(leaf: str) -> str:
    return _TRANSLIT.get(leaf, re.sub(r"\W+", "_", leaf))


def main() -> None:
    # ---- Work 1: రాధికాసాంత్వనము (ముద్దుపళని), 1953 — transcluded chapters ----
    radhika_main = "రాధికాసాంత్వనము (ముద్దుపళని)"
    radhika_chapters = ["ప్రథమాశ్వాసము", "ద్వితీయాశ్వాసము", "తృతీయాశ్వాసము", "చతుర్థాశ్వాసము"]
    print("=== Crawling రాధికాసాంత్వనము (ముద్దుపళని) ===")
    crawl_transcluded_work(radhika_main, "radhikasantvanamu", radhika_chapters)

    # ---- Work 2: శృంగారామరుకావ్యము (వేటూరి ప్రభాకరశాస్త్రి) — Page: range /1..16 ----
    print("\n=== Crawling శృంగారామరుకావ్యము (వేటూరి ప్రభాకరశాస్త్రి) ===")
    crawl_page_range(
        base="Srungaramaruka Kavyam By Veturi Prabhakara Sastry In Telugu.pdf",
        lo=1, hi=16, slug="srungaramaruka_kavyam",
        title_human="శృంగారామరుకావ్యము — వేటూరి ప్రభాకరశాస్త్రి",
    )

    # ---- Work 3: తరికొండ నృసింహశతకము (తరిగొండ వేంగమాంబ) — padyam + bhāvaṃ ----
    print("\n=== Crawling తరికొండ నృసింహశతకము (తరిగొండ వేంగమాంబ) ===")
    crawl_single_page(
        title="తరికొండ నృసింహశతకము/తరిగొండ నృసింహశతకము",
        slug="tarikonda_nrusimha_satakam",
        title_human="తరికొండ నృసింహశతకము (పద్యం + భావం) — తరిగొండ వేంగమాంబ",
    )


if __name__ == "__main__":
    sys.exit(main())
