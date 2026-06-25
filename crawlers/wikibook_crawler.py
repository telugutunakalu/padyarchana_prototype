#!/usr/bin/env python3
"""Unified Wikisource book crawler → padyarchana JSON (padyalu_json_data/).

Auto-handles the structural variety found across many te.wikisource books:
  * chapter discovery via the allpages API (link-based TOCs badly undercount);
  * content vs front-matter (పీఠిక/విషయసూచిక/…) classification;
  * per-page clean-vs-OCR detection (newline density) →
        clean → text_to_json.parse_padyalu  (markers, సీసము+గీత merge, prose skip)
        OCR   → salvage_parse                (tight filter: discernible verses only)
  * per-book overrides: శ్రీ-prepend of each ఆశ్వాసము's unmarked opening padyam.

Metadata (author/year) + the content-chapter list come from a discovery manifest;
literary form is inferred from the title. OCR-salvaged books get flag=OCR-sourced.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wikisource_crawler as w  # noqa: E402
import text_to_json as t  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "padyalu_json_data"
MANIFEST = json.load(open(ROOT / "crawlers" / "wikibook_manifest.json", encoding="utf-8"))

# ---- subpage classification -------------------------------------------------
FRONT = re.compile(
    r"పీఠిక|విషయసూచిక|సూచిక|ఉపోద్ఘాత|భూమిక|విజ్ఞప్తి|మున్నుడి|ఆవాహన|శుద్ధ|ప్రస్తావన"
    r"|నివేదన|పరిశిష్ట|ప్రకాశక|విజ్ఞాపన|తొలి|ముందుమాట|మనవి|Introduction|Foreword"
    r"|వంశవృక్ష|కృతిసమాలోక|ముఖపత్ర")
JUNK = re.compile(r"^\d+\s*వ?\s*పుట$|చివరి|పుటలు|^\d+$")


def all_subpages(work: str) -> list[str]:
    out: list[str] = []
    cont: dict = {}
    for _ in range(30):
        w._throttle()
        p = {"action": "query", "list": "allpages", "apprefix": work + "/",
             "apnamespace": "0", "aplimit": "500", "format": "json", "formatversion": 2}
        p.update(cont)
        d = w._session().get(w.API, params=p, timeout=60).json()
        out += [x["title"].split("/", 1)[1] for x in d["query"]["allpages"]]
        if "continue" in d:
            cont = d["continue"]
        else:
            break
    return out


def content_chapters(work: str) -> list[str]:
    return [s for s in all_subpages(work) if not FRONT.search(s) and not JUNK.search(s)]


# ---- quality ----------------------------------------------------------------
def is_ocr(text: str) -> bool:
    return bool(text) and text.count("\n") / max(1, len(text)) <= 0.004


# ---- OCR salvage parser (tight: discernible verses only) --------------------
_S_METER = {"శా": "శార్దూలవిక్రీడితము", "సీ": "సీసము", "మత్త": "మత్తకోకిల",
            "తే": "తేటగీతి", "గీ": "గీతము", "మాలి": "మాలిని", "స్రగ్ధ": "స్రగ్ధర",
            "చ": "చంపకమాల", "ఉ": "ఉత్పలమాల", "మ": "మత్తేభవిక్రీడితము",
            "క": "కందము", "ఆ": "ఆటవెలది", "వ": "వచనము"}
_S_ALT = "|".join(sorted(_S_METER, key=len, reverse=True))
_S_MARK = re.compile(rf"(?<![ఀ-౿])({_S_ALT})\s*(?:॥|\|\|?)")
_S_PADAM = re.compile(r"[|!।॥]+")
_S_NUM = re.compile(r"[0-9౦-౯]+")
_TEL = re.compile(r"[ఀ-౿]")
_ASV = ("ప్రథమ ద్వితీయ తృతీయ చతుర్థ పంచమ షష్ఠ సప్తమ అష్టమ నవమ దశమ ఏకాదశ ద్వాదశ").split()
# generic chapter/invocation noise to strip from salvaged lines
_S_LEAK = re.compile(
    r"కథాప్రారంభము|అవతారిక|" + "|".join(a + "ాశ్వాసము" for a in _ASV) +
    r"|బాలకాండము|అయోధ్యాకాండము|ఆరణ్యకాండము|కిష్కింధాకాండము|సుందరకాండము|యుద్ధకాండము"
    r"|[A-Za-z]+|[+*]\d*")


def _s_clean(s: str, title_re: re.Pattern) -> str:
    s = title_re.sub(" ", s)
    s = _S_LEAK.sub(" ", s)
    s = re.sub(r"[^ఀ-౿\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _telugu_ratio(s: str) -> float:
    ns = [c for c in s if not c.isspace()]
    return len(_TEL.findall(s)) / len(ns) if ns else 0.0


def salvage_parse(text: str, chapter, work: str) -> list[dict]:
    # strip the running-title spine + common invocations
    spine = re.compile(re.escape(work) + r"[.\s]*|" + r"\s*".join(re.escape(c) for c in work) + r"[.\s]*"
                       + r"|శ్రీ\s*శ్రీధరాయనమ\S*|శివాభ్యాంనమః|శ్రీశారదామ్బాయై\s*నమః|శ్రీగురుభ్యోనమ\S*")
    text = spine.sub(" ", text)
    title_strip = re.compile(re.escape(work) + r"|" + r"\s*".join(re.escape(c) for c in work))
    ms = list(_S_MARK.finditer(text))
    poems: list[dict] = []
    for i, m in enumerate(ms):
        block = text[m.end(): ms[i + 1].start() if i + 1 < len(ms) else len(text)]
        nums = _S_NUM.findall(block)
        number = int(nums[-1]) if nums and nums[-1].isdigit() else "unknown"
        if number == 0:
            number = "unknown"
        body = re.sub(r"[॥|।\s]*[0-9౦-౯]+[.\s]*$", "", block)
        lines = [_s_clean(p, title_strip) for p in _S_PADAM.split(body)]
        lines = [ln for ln in lines if len(ln) >= 6 and _telugu_ratio(ln) >= 0.85]
        chandassu = _S_METER[m.group(1)]
        if number == "unknown" or chandassu == "వచనము":
            continue
        lo, hi = (6, 9) if chandassu == "సీసము" else (4, 4)
        if not (lo <= len(lines) <= hi) or sum(len(x) for x in lines) < 50:
            continue
        avg = sum(len(x) for x in lines) / len(lines)
        if max(len(x) for x in lines) > 3 * avg or max(len(x) for x in lines) > (135 if chandassu == "సీసము" else 95):
            continue
        poems.append({"lines_telugu": lines, "Chandassu": chandassu, "chapter": chapter,
                      "padyam_number": number, "bhavam": None, "prathipadartham": None})
    return poems


# ---- marker-less numbered-verse fallback (śatakams, నీతి verses) ------------
# Clean works whose padyalu carry NO line-initial meter marker but DO end with a
# verse number (often after a makutam line). Group lines into verses by number.
_TRAILNUM = re.compile(r"[\s|।॥]+([0-9౦-౯]+)\s*[.|।॥]*$")
# colophon / attribution / TOC-leader noise that can bleed into a verse buffer
_NV_NOISE = re.compile(r'["“”]|రచించ|వ్రాస|ముద్రి|[A-Za-z]|\.\s*\.\s*\.|^శ్రీ$|Rights')


def parse_numbered_verses(text: str, chapter) -> list[dict]:
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines() if ln.strip()]
    groups: list[list[str]] = []
    buf: list[str] = []
    for ln in lines:
        if re.fullmatch(r"[0-9౦-౯]+", ln):           # standalone verse number
            if buf:
                groups.append(buf[:])
                buf = []
            continue
        m = _TRAILNUM.search(ln)
        if m:                                          # number at end of last padam
            head = ln[:m.start()].strip()
            if head:
                buf.append(head)
            groups.append(buf[:])
            buf = []
        else:
            buf.append(ln)
    out: list[dict] = []
    for g in groups:
        g = [x for x in g if len(x) >= 4 and _TEL.search(x) and not _NV_NOISE.search(x)]
        if len(g) > 7:        # buffer ran into front-matter/prose — keep the verse tail
            g = g[-4:]
        if not (2 <= len(g) <= 7) or sum(len(x) for x in g) < 40:
            continue
        out.append({"lines_telugu": g, "Chandassu": "unknown", "chapter": chapter,
                    "padyam_number": "unknown", "bhavam": None, "prathipadartham": None})
    return out


# ---- ద్విపద (couplet) parser ------------------------------------------------
# ద్విపద works are a continuous stream of rhyming couplets with NO meter markers
# and NO verse numbers. In the rendered HTML the couplet పాదాలు live inside
# <div class="poem"> blocks (<br/>-separated lines); section headings (రాగము …,
# topic titles) are <p class="pclass"> *outside* those blocks, and trailing
# glossary appendices aren't in poem blocks at all — so we segment by taking
# each poem block's lines and pairing them two-at-a-time from the top.
import html as _htmllib  # noqa: E402


def fetch_html(title: str) -> str:
    for a in range(5):
        try:
            w._throttle()
            r = w._session().get(w.API, params={"action": "parse", "page": title,
                "prop": "text", "format": "json", "formatversion": 2,
                "disablelimitreport": 1}, timeout=60)
            if r.status_code == 429:
                time.sleep(5 * (a + 1))
                continue
            d = r.json()
            return "" if "error" in d else d["parse"]["text"]
        except Exception:
            time.sleep(2 * (a + 1))
    return ""


def _poem_blocks(html: str) -> list[str]:
    blocks: list[str] = []
    for m in re.finditer(r'<div class="poem">', html):
        i = m.end()
        depth, j = 1, i
        while depth and j < len(html):
            nd, ndc = html.find("<div", j), html.find("</div>", j)
            if ndc == -1:
                break
            if nd != -1 and nd < ndc:
                depth += 1
                j = nd + 4
            else:
                depth -= 1
                j = ndc + 6
        blocks.append(html[i:j - 6])
    return blocks


def _strip_html_line(s: str) -> str:
    s = re.sub(r"<sup[^>]*>.*?</sup>", "", s, flags=re.S)   # footnote refs
    s = re.sub(r"<style[^>]*>.*?</style>", "", s, flags=re.S)
    s = re.sub(r"<[^>]+>", "", s)
    s = _htmllib.unescape(s)
    s = re.sub(r"[0-9౦-౯]+\s*$", "", s.strip())            # trailing line-number
    return re.sub(r"\s+", " ", s).strip()


# title-page / colophon lines that can appear inside a front-matter poem block
_DW_NOISE = re.compile(r"రచింపబడ|రచించ|వారిచేత|గారిచేత|ముద్రి|ప్రెస్|ప్రతి|వెల|రూపాయ"
                       r"|సంపాదక|[A-Za-z]|మ॥|రా॥|పంతుల")


def parse_dwipada(title: str, chapter) -> list[dict]:
    html = fetch_html(title)
    out: list[dict] = []
    for block in _poem_blocks(html):
        raw = re.sub(r"</?p[^>]*>", "\n", block)
        lines: list[str] = []
        for chunk in re.split(r"<br\s*/?>", raw):
            for sub in chunk.split("\n"):
                ln = _strip_html_line(sub)
                if len(ln) >= 4 and _TEL.search(ln) and not _DW_NOISE.search(ln):
                    lines.append(ln)
        for k in range(0, len(lines), 2):
            pair = lines[k:k + 2]
            if pair and sum(len(x) for x in pair) >= 15:
                out.append({"lines_telugu": pair, "Chandassu": "ద్విపద", "chapter": chapter,
                            "padyam_number": "unknown", "bhavam": None, "prathipadartham": None})
    return out


# ---- block (song) parser ----------------------------------------------------
# For marker-less, number-less metered SONG works (గీతాంజలి, గీతావళి) the only
# reliable verse boundary is the <p> block inside <div class="poem">. Each <p>
# is one song-stanza; the ♦ inside a line is just a yati (caesura) mark.
def parse_blocks(title: str, chapter) -> list[dict]:
    html = fetch_html(title)
    out: list[dict] = []
    for block in _poem_blocks(html):
        for p in re.findall(r"<p>(.*?)</p>", block, re.S):
            lines: list[str] = []
            for chunk in re.split(r"<br\s*/?>", p):
                ln = _strip_html_line(chunk).replace("♦", " ")
                ln = re.sub(r"\s+", " ", ln).strip()
                if len(ln) >= 4 and _TEL.search(ln) and not _DW_NOISE.search(ln):
                    lines.append(ln)
            if len(lines) >= 2 and sum(len(x) for x in lines) >= 30:
                out.append({"lines_telugu": lines, "Chandassu": "unknown", "chapter": chapter,
                            "padyam_number": "unknown", "bhavam": None, "prathipadartham": None})
    return out


# ---- śrī-prepend opening padyam (rameswara-style) ---------------------------
_NUMLINE = re.compile(r"^[0-9౦-౯]+$")


def first_padyam(text: str, chapter: str) -> dict | None:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if chapter not in lines:
        return None
    out: list[str] = []
    for ln in lines[lines.index(chapter) + 1:]:
        if _NUMLINE.match(ln) or t._marker(ln):
            break
        out.append(ln)
    if len(out) < 2:
        return None
    if not out[0].startswith("శ్రీ"):
        out[0] = "శ్రీ" + out[0]
    meter = "కందము" if len(out[0]) < 22 else "unknown"
    return {"lines_telugu": out, "Chandassu": meter, "chapter": chapter,
            "padyam_number": 1, "bhavam": None, "prathipadartham": None}


# ---- Page: namespace fallback (orphaned proofread content) ------------------
# Some works assemble only a cover into the main namespace; the verses live only
# as individual proofread Page: pages (పుట:Index.pdf/N). Gather the *existing*
# proofread pages (proofreading is often partial → scattered page numbers).
_PAGES_TAG = re.compile(r'<pages\s+index="([^"]+)"')


def _wikitext(title: str) -> str:
    for a in range(4):
        try:
            w._throttle()
            r = w._session().get(w.API, params={"action": "parse", "page": title,
                "prop": "wikitext", "format": "json", "formatversion": 2}, timeout=60)
            if r.status_code == 429:
                time.sleep(5 * (a + 1))
                continue
            d = r.json()
            return "" if "error" in d else d["parse"]["wikitext"]
        except Exception:
            time.sleep(2 * (a + 1))
    return ""


def _index_pdfs(work: str, chapters: list[str]) -> list[str]:
    pdfs: list[str] = []
    for title in [work] + [f"{work}/{c}" for c in chapters]:
        for m in _PAGES_TAG.finditer(_wikitext(title)):
            if m.group(1) not in pdfs:
                pdfs.append(m.group(1))
    return pdfs


def _page_ns_titles(pdf: str) -> list[str]:
    out: list[str] = []
    cont: dict = {}
    for _ in range(10):
        w._throttle()
        p = {"action": "query", "list": "allpages", "apprefix": pdf + "/",
             "apnamespace": 104, "aplimit": "500", "format": "json", "formatversion": 2}
        p.update(cont)
        d = w._session().get(w.API, params=p, timeout=60).json()
        out += [x["title"] for x in d["query"]["allpages"]]
        if "continue" in d:
            cont = d["continue"]
        else:
            break
    return sorted(out, key=lambda x: int(re.sub(r"\D", "", x.rsplit("/", 1)[1]) or 0))


def page_ns_text(work: str, chapters: list[str]) -> str:
    parts: list[str] = []
    for pdf in _index_pdfs(work, chapters):
        for tp in _page_ns_titles(pdf):
            body = w.fetch_rendered(tp)
            if body.strip():
                parts.append(body)
    return "\n".join(parts)


# ---- per-book crawl ---------------------------------------------------------
def infer_form(title: str) -> str:
    if "శతక" in title:
        return "శతకము"
    if "ద్విపద" in title:
        return "ద్విపద"
    if "దండక" in title:
        return "దండకము"
    if "పురాణ" in title or "ఖండ" in title:
        return "పురాణము"
    if "రామాయణ" in title or "భారత" in title or "హరివంశ" in title:
        return "ఇతిహాసకావ్యము"
    return "ప్రబంధము"


def crawl_book(rec: dict) -> dict:
    work = rec["work"]
    chapters = rec.get("content_subs") or []
    pages = [(f"{work}/{c}", c) for c in chapters] if chapters else [(work, None)]
    all_poems: list[dict] = []
    ocr_pages = 0
    for ptitle, chapter in pages:
        if rec.get("dwipada"):       # continuous couplet stream → pair from HTML
            all_poems.extend(parse_dwipada(ptitle, chapter))
            time.sleep(0.3)
            continue
        if rec.get("blocks"):        # marker-less song work → <p> block per stanza
            all_poems.extend(parse_blocks(ptitle, chapter))
            time.sleep(0.3)
            continue
        text = w.fetch_rendered(ptitle)
        if not text:
            continue
        if rec.get("force_ocr") or is_ocr(text):
            all_poems.extend(salvage_parse(text, chapter, work))
            ocr_pages += 1
        else:
            if rec.get("sri_prepend") and chapter:
                fp = first_padyam(text, chapter)
                if fp:
                    all_poems.append(fp)
            ps = t.parse_padyalu(text, fixed_chapter=chapter)
            if not ps:  # marker-less work (śatakam / numbered నీతి verses)
                ps = parse_numbered_verses(text, chapter)
            all_poems.extend(ps)
        time.sleep(0.3)
    pagens_used = False
    if len(all_poems) < 10 and not rec.get("force_ocr"):
        # main namespace assembled little — try orphaned proofread Page: pages
        pn = page_ns_text(work, chapters)
        if pn:
            alt = t.parse_padyalu(pn)
            if not alt:
                alt = parse_numbered_verses(pn, None)
            if is_ocr(pn) and len(alt) < 5:
                alt = salvage_parse(pn, None, work)
            if len(alt) > len(all_poems):
                all_poems = alt
                pagens_used = is_ocr(pn)
                if pagens_used:
                    ocr_pages = len(pages)
    all_poems = [{"id": i, **p} for i, p in enumerate(all_poems, 1)]
    record = {
        "shatakam_title_telugu": work,
        "author_telugu": rec.get("author") or "unknown",
        "year": rec.get("year") or "unknown",
        "literary_form_telugu": infer_form(work),
        "source_url": "https://te.wikisource.org/wiki/" + work,
        "poems": all_poems,
    }
    if ocr_pages >= max(1, len(pages)) / 2 and ocr_pages:
        record["flag"] = "OCR-sourced"
        record["note"] = "Salvaged from an unproofread OCR; verse text is OCR-garbled."
    OUT.mkdir(exist_ok=True)
    fp = OUT / (rec["slug"] + ".json")
    fp.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  -> {fp.name}: {len(all_poems)} padyalu "
          f"({len(pages)} pages, {ocr_pages} ocr){' [OCR]' if 'flag' in record else ''}", flush=True)
    return {"slug": rec["slug"], "work": work, "padyalu": len(all_poems),
            "pages": len(pages), "ocr_pages": ocr_pages}


def main() -> None:
    only = sys.argv[1] if len(sys.argv) > 1 else None
    results = []
    for rec in MANIFEST:
        if rec.get("status") != "ok":
            continue
        if only and only not in (rec["slug"], rec["work"]):
            continue
        print(f"\n## {rec['work']} ({rec.get('author')})", flush=True)
        results.append(crawl_book(rec))
    print(f"\n=== TOTAL: {sum(r['padyalu'] for r in results)} padyalu across {len(results)} books ===")
    json.dump(results, open(ROOT / "crawlers" / "wikibook_results.json", "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
