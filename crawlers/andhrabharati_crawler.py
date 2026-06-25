#!/usr/bin/env python3
"""Crawl అనంతామాత్యుని ఛందోదర్పణము from andhrabharati.com and emit a
padyarchana-compatible JSON into padyalu_json_data/.

Unlike the Wikisource crawler, andhrabharati pages are table-structured: each
named section (<a name="NNN">) is a <table> whose rows are
    [ <td> meter-abbr ] [ <td nowrap> verse lines (<br>-separated) ] [ <td> number ]
with the first row being the section title. This is far cleaner to parse than
line-marker text, so we read the table directly.

Notes on the site:
  * needs a full browser User-Agent + Referer or it returns 502;
  * its TLS chain doesn't validate against the local CA bundle (verify=False);
  * verse text carries stray "\\" before word-final consonants (an encoding
    artifact — stripped) and U+200C ZWNJ (kept; the existing corpus uses it).
"""
from __future__ import annotations

import html as _html
import json
import re
import time
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SITE = "https://www.andhrabharati.com"
OUT = Path(__file__).resolve().parent.parent / "padyalu_json_data"

# andhrabharati works that share the same table-structured layout. `path` is
# the URL folder; chapters are discovered from the work's index unless `pages`
# explicitly lists (filename, chapter-name) — needed when the index links are
# incomplete. `form` defaults to ఛందోగ్రంథము.
WORKS = [
    dict(path="bhAshha/ChaMdassu/ChaMdOdarpaNamu", slug="chandodarpanamu_anantamatya",
         title="ఛందోదర్పణము", author="అనంతామాత్యుడు"),
    dict(path="bhAshha/ChaMdassu/sulakShaNasAramu", slug="sulakshanasaramu_lingamagunta_timmakavi",
         title="సులక్షణసారము", author="లింగమగుంట తిమ్మకవి"),
    dict(path="bhAshha/nighaMTuvulu/AMdhranAmasaMgrahamu", slug="andhranamasangrahamu_paidipati_lakshmanakavi",
         title="ఆంధ్రనామసంగ్రహము", author="పైడిపాటి లక్ష్మణకవి", form="నిఘంటువు",
         pages=[("avatArika.html", "అవతారిక"), ("dEvavargu.html", "దేవవర్గు"),
                ("mAnavavargu.html", "మానవవర్గు"), ("sthAvaravargu.html", "స్థావరవర్గు"),
                ("tiryagvargu.html", "తిర్యగ్వర్గు"), ("nAnArthavargu.html", "నానార్థవర్గు")]),
    dict(path="bhAshha/nighaMTuvulu/AMdhranAmashEShamu", slug="andhranamaseshamu_adidamu_surakavi",
         title="ఆంధ్రనామశేషము", author="అడిదము సూరకవి", form="నిఘంటువు",
         pages=[("index.html", None)]),  # single page: content is inline on the index
    dict(path="bhAshha/nighaMTuvulu/sAMbanighaMTuvu", slug="sambanighantuvu",
         title="సాంబనిఘంటువు", author="కస్తూరి రంగకవి", form="నిఘంటువు",
         pages=[("avatArika.html", "అవతారిక"), ("dEvavargu.html", "దేవవర్గు"),
                ("mAnavavargu.html", "మానవవర్గు"), ("sthAvaravargu.html", "స్థావరవర్గు"),
                ("tiryagvargu.html", "తిర్యగ్వర్గు"), ("nAnArthavargu.html", "నానార్థవర్గు")]),
    dict(path="itihAsamulu/rAmAyaNamu", slug="molla_ramayanamu", form="మహాకావ్యము",
         subpages=True,  # each kāṇḍa page is a TOC of leaf verse pages
         title="మొల్ల రామాయణము", author="ఆతుకూరి మొల్ల",
         pages=[("avatArika.html", "అవతారిక"), ("bAla.html", "బాలకాండము"),
                ("ayOdhya.html", "అయోధ్యాకాండము"), ("araNya.html", "అరణ్యకాండము"),
                ("kiShkiMdha.html", "కిష్కింధాకాండము"), ("suMdara.html", "సుందరకాండము"),
                ("yuddha1.html", "యుద్ధకాండము - ప్రథమాశ్వాసము"),
                ("yuddha2.html", "యుద్ధకాండము - ద్వితీయాశ్వాసము"),
                ("yuddha3.html", "యుద్ధకాండము - తృతీయాశ్వాసము")]),
    dict(path="itihAsamulu/UttaraRamayanamu", slug="uttara_ramayanamu_kankanti_paparaju",
         title="ఉత్తరరామాయణము", author="కంకంటి పాపరాజు", form="మహాకావ్యము",
         subpages=True,
         pages=[("UR_pIThika.html", "పీఠిక"), ("UR_prathama.html", "ప్రథమాశ్వాసము"),
                ("UR_dvitIya.html", "ద్వితీయాశ్వాసము"), ("UR_tRutIya.html", "తృతీయాశ్వాసము"),
                ("UR_caturtha.html", "చతుర్థాశ్వాసము"), ("UR_pancama.html", "పంచమాశ్వాసము"),
                ("UR_ShaShTha.html", "షష్ఠాశ్వాసము"), ("UR_saptama.html", "సప్తమాశ్వాసము"),
                ("UR_aShTama.html", "అష్టమాశ్వాసము")]),
    dict(path="itihAsamulu/AchchaTeluguRamayanamu", slug="achchatelugu_ramayanamu_kuchimanchi_timmakavi",
         title="అచ్చతెలుఁగు రామాయణము", author="కూచిమంచి తిమ్మకవి", form="మహాకావ్యము",
         pages=[("Pithika.html", "పీఠిక"), ("BalaKanda.html", "బాలకాండము"),
                ("AyodhyaKanda.html", "అయోధ్యాకాండము"), ("AranyaKanda.html", "అరణ్యకాండము"),
                ("KishkindhaKanda.html", "కిష్కింధాకాండము"), ("SundaraKanda.html", "సుందరకాండము"),
                ("YuddhaKanda.html", "యుద్ధకాండము")]),  # each page is direct content
    dict(path="kAvyamulu/manu", slug="manucharitra_allasani_peddana",
         title="మను చరిత్రము", author="అల్లసాని పెద్దన", form="ప్రబంధము",
         grouped_index=True),  # single index groups leaf links under ఆశ్వాసము headers
    dict(path="kAvyamulu/vijayavilAsamu", slug="vijayavilasamu_chemakura_venkatakavi",
         title="విజయ విలాసము", author="చేమకూర వేంకటకవి", form="ప్రబంధము",
         grouped_index=True),
    # andhrabharati version (better-formatted) to override the Wikisource one;
    # title matches the existing DB source. Each ఆశ్వాసము page is direct content.
    dict(path="kAvyamulu/SivarAtrimAhAtmyamu", slug="sivaratrimahatmyamu_srinatha_andhrabharati",
         title="శివరాత్రిమాహాత్మ్యము", author="శ్రీనాథుడు", form="ప్రబంధము",
         pages=[("01.html", "ప్రథమాశ్వాసము"), ("02.html", "ద్వితీయాశ్వాసము"),
                ("03.html", "తృతీయాశ్వాసము"), ("04.html", "చతుర్థాశ్వాసము"),
                ("05.html", "పంచమాశ్వాసము")]),
    dict(path="kAvyamulu/pArijAtApaharaNamu", slug="parijatapaharanamu_mukku_timmana",
         title="పారిజాతాపహరణము", author="ముక్కు తిమ్మన", form="ప్రబంధము",
         grouped_index=True),
    dict(path="kAvyamulu/AndhraPuranamu", slug="andhrapuranamu_madhunapantula_satyanarayanasastri",
         title="ఆంధ్రపురాణము", author="మధునాపంతుల సత్యనారాయణ శాస్త్రి", form="కావ్యము",
         pages=[("Avatarika.html", "అవతారిక"), ("UdayaParvamu.html", "ఉదయ పర్వము"),
                ("SatavahanaParvamu.html", "సాతవాహన పర్వము"), ("ChalukyaParvamu.html", "చాళుక్య పర్వము"),
                ("KakatiyaParvamu.html", "కాకతీయ పర్వము"), ("PunahpratishtaParvamu.html", "పునఃప్రతిష్ఠా పర్వము"),
                ("VidyanagaraParvamu.html", "విద్యానగర పర్వము"), ("SrikrishnadevarayaParvamu.html", "శ్రీకృష్ణదేవరాయ పర్వము"),
                ("VijayaParvamu.html", "విజయ పర్వము"), ("NayakarajaParvamu.html", "నాయకరాజ పర్వము")]),
    # === Public-domain single-page works using the flexible 1/2/3-cell parser ===
    # ముసలమ్మ మరణము — కట్టమంచి రామలింగారెడ్డి (d. 1951). Mixed 3-cell (most rows)
    # and 1-cell prose passages. Standard meter abbrevs in cell 0.
    dict(path="kAvyamulu/musalamma_maraNamu", slug="musalamma_maranamu_kattamanchi_ramalinga_reddy",
         title="ముసలమ్మ మరణము", author="కట్టమంచి రామలింగారెడ్డి", form="ఖండకావ్యము",
         single_page=True, flexible=True),
    # తెలుఁగునాడు — దాసు శ్రీరాములు (d. 1908). 2-cell layout: cell 0 = meter,
    # cell 1 = verse lines. No per-padyam numbering — numbered by stream position.
    dict(path="kAvyamulu/telugunADu", slug="telugunadu_dasu_sriramulu",
         title="తెలుఁగునాడు", author="దాసు శ్రీరాములు", form="ఖండకావ్యము",
         single_page=True, flexible=True),
    # పానశాల — దువ్వూరి రామిరెడ్డి (d. 1947). Mixed 1/2/3-cell. 2-cell rows
    # are [verse | number] (no meter cell); 3-cell are [meter | verse | number].
    dict(path="kAvyamulu/pAnaSAla", slug="panasala_duvvuri_rami_reddy",
         title="పానశాల", author="దువ్వూరి రామిరెడ్డి", form="ఖండకావ్యము",
         single_page=True, flexible=True),
]
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "te,en;q=0.9",
    "Referer": f"{SITE}/index.html",
}

# meter-abbreviation (cell 1) -> full chandassu name
MARKERS = {
    "క": "కందము", "సీ": "సీసము", "ఆ": "ఆటవెలది", "తే": "తేటగీతి", "గీ": "గీతము",
    "చ": "చంపకమాల", "ఉ": "ఉత్పలమాల", "మ": "మత్తేభవిక్రీడితము",
    "శా": "శార్దూలవిక్రీడితము", "వ": "వచనము", "ద్వి": "ద్విపద", "రగడ": "రగడ",
    "మం": "మంజరి", "తరు": "తరువోజ", "అ": "అక్కర",
    # source vowel-length / spelling / stacked variants of the above abbrevs
    "సి": "సీసము", "కా": "కందము", "కం": "కందము",
    "తె": "తేటగీతి", "తీ": "తేటగీతి", "తే.గీ": "తేటగీతి",
    "ఆట": "ఆటవెలది", "ఆ.వె": "ఆటవెలది", "చం": "చంపకమాల", "తరలం": "తరలము",
    "శ": "శార్దూలవిక్రీడితము",  # variant of శా.
}
_unmapped: set[str] = set()


def fetch(url: str, retries: int = 4) -> str:
    last = None
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, verify=False, timeout=60)
            if r.status_code == 200 and len(r.content) > 500:
                r.encoding = "utf-8"
                return r.text
            last = f"HTTP {r.status_code} len={len(r.content)}"
        except Exception as e:  # noqa: BLE001
            last = e
        time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"failed to fetch {url}: {last}")


def fetch_optional(url: str) -> str | None:
    """Single-attempt fetch; return None for 404/empty (used to probe for the
    end of a sequential leaf-page range)."""
    try:
        r = requests.get(url, headers=HEADERS, verify=False, timeout=60)
        if r.status_code == 200 and len(r.content) > 500:
            r.encoding = "utf-8"
            return r.text
    except Exception:  # noqa: BLE001
        pass
    return None


def _clean(text: str) -> str:
    text = _html.unescape(text)
    text = text.replace("\\", "")          # stray backslash artifact
    text = re.sub(r"\[\d+\]", "", text)    # editorial footnote ref markers
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _cell_text(td_inner: str) -> str:
    # strip any inner tags except using <br> as line break already handled
    return _clean(re.sub(r"<[^>]+>", "", td_inner))


def _chandassu(marker_raw: str) -> str:
    m = _clean(re.sub(r"<[^>]+>", "", marker_raw)).rstrip(".।॥ ").strip()
    if not m:
        return "unknown"
    if m in MARKERS:
        return MARKERS[m]
    _unmapped.add(m)
    return m  # keep the raw label (often itself a meter name in a chandas text)


def _numeric_only(s: str) -> bool:
    """Cell is just a verse number (digits, optional brackets/dots)."""
    s = s.strip()
    return bool(s) and bool(re.fullmatch(r"\[?\d+\]?\.?", s))


def parse_chapter_flexible(htmltext: str, chapter: str,
                           section_override: str | None = None) -> list[dict]:
    """Like parse_chapter, but handles 1-, 2-, and 3-cell verse rows.

    The disambiguation rules:
      * 3 cells → [meter, verse, number]    (same as the classical layout)
      * 2 cells, last cell is numeric → [verse, number]   (no meter shown)
      * 2 cells, last cell is text   → [meter, verse]     (no number shown)
      * 1 cell → entire row is verse body, no meter or number

    When meter is absent (1-cell rows, or 2-cell rows without a meter cell),
    we tag the padyam as "వచనం" — author-direction fallback for free-verse-
    style passages that the source doesn't classify.
    """
    poems: list[dict] = []
    for tbl in re.findall(r"<table[^>]*>(.*?)</table>", htmltext, re.S | re.I):
        rows = re.findall(r"(<tr[^>]*>)(.*?)</tr>", tbl, re.S | re.I)
        section = section_override
        for tr_open, row in rows:
            bg = (re.search(r"bgcolor=['\"]?#?([0-9a-fA-F]{6})", tr_open) or [None, ""])[1].lower()
            if bg == "eedddd":
                hc = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S | re.I)
                if hc:
                    section = _cell_text(hc[0]) or section
                continue
            if bg not in ("ffffcc", "eeeecc"):
                continue
            cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S | re.I)
            if not cells:
                continue

            marker_raw: str = ""
            body_raw: str = ""
            num_raw: str = ""

            if len(cells) >= 3:
                # Standard classical layout is [meter | verse | number],
                # but some works (e.g. పానశాల) shift to [number | verse | …].
                # If cell 0 is purely numeric, treat it as the verse number
                # and assume the body is in cell 1.
                if _numeric_only(_cell_text(cells[0])):
                    num_raw, body_raw = cells[0], cells[1]
                else:
                    marker_raw, body_raw, num_raw = cells[0], cells[1], cells[2]
            elif len(cells) == 2:
                last_text = _cell_text(cells[1])
                if _numeric_only(last_text):
                    body_raw, num_raw = cells[0], cells[1]
                else:
                    marker_raw, body_raw = cells[0], cells[1]
            else:  # 1 cell
                body_raw = cells[0]

            lines = [_cell_text(x) for x in re.split(r"<br\s*/?>", body_raw, flags=re.I)]
            lines = [ln for ln in lines if ln]
            if not lines:
                continue

            if marker_raw.strip():
                chandassu = _chandassu(marker_raw)
            else:
                # No meter cell — modern free-verse fallback. Use the
                # canonical form already present in the DB (వచనము) instead
                # of the surface form వచనం so we don't create a duplicate
                # meter row at import time.
                chandassu = "వచనము"

            num_txt = _cell_text(num_raw).strip("[]. ")
            poems.append({
                "lines_telugu": lines,
                "Chandassu": chandassu,
                "chapter": chapter,
                "section": section,
                "padyam_number": int(num_txt) if num_txt.isdigit() else "unknown",
                "bhavam": None,
                "prathipadartham": None,
            })
    return _merge_sisa(poems)


def parse_chapter(htmltext: str, chapter: str, section_override: str | None = None) -> list[dict]:
    poems: list[dict] = []
    # each section is a <table ...> ... </table> introduced by <a name="N">
    for tbl in re.findall(r"<table[^>]*>(.*?)</table>", htmltext, re.S | re.I):
        rows = re.findall(r"(<tr[^>]*>)(.*?)</tr>", tbl, re.S | re.I)
        if not rows:
            continue
        # leaf pages without a title row fall back to the TOC heading; pages
        # with their own #eedddd rows override it as they are encountered
        section = section_override
        for tr_open, row in rows:
            bg = (re.search(r"bgcolor=['\"]?#?([0-9a-fA-F]{6})", tr_open) or [None, ""])[1].lower()
            # section title rows are #eedddd; verse rows are #ffffcc / #eeeecc.
            # any other row (nav, breadcrumb, footer) is skipped.
            if bg == "eedddd":
                hc = re.findall(r"<td[^>]*colspan[^>]*>(.*?)</td>", row, re.S | re.I)
                if hc:
                    section = _cell_text(hc[0]) or None
                continue
            if bg not in ("ffffcc", "eeeecc"):
                continue
            cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S | re.I)
            if len(cells) < 3:
                continue
            marker, body, num = cells[0], cells[1], cells[2]
            # split verse body on <br>
            lines = [_cell_text(x) for x in re.split(r"<br\s*/?>", body, flags=re.I)]
            lines = [ln for ln in lines if ln]
            if not lines:
                continue
            num_txt = _cell_text(num)
            poems.append({
                "lines_telugu": lines,
                "Chandassu": _chandassu(marker),
                "chapter": chapter,
                "section": section,
                "padyam_number": int(num_txt) if num_txt.isdigit() else "unknown",
                "bhavam": None,
                "prathipadartham": None,
            })
    return _merge_sisa(poems)


_GITA_NAMES = {"తేటగీతి", "గీతము", "ఆటవెలది"}


def _merge_sisa(poems: list[dict]) -> list[dict]:
    """A సీసము padyam is laid out as two table rows: the సీ. body (no verse
    number) followed by its తే./గీ./ఆ. conclusion (which carries the number).
    Fold the pair back into a single సీసము padyam."""
    out: list[dict] = []
    i = 0
    while i < len(poems):
        p = poems[i]
        nxt = poems[i + 1] if i + 1 < len(poems) else None
        if (p["Chandassu"] == "సీసము" and p["padyam_number"] == "unknown"
                and nxt and nxt["Chandassu"] in _GITA_NAMES):
            p["lines_telugu"] = p["lines_telugu"] + nxt["lines_telugu"]
            p["padyam_number"] = nxt["padyam_number"]
            if not p.get("section"):
                p["section"] = nxt.get("section")
            out.append(p)
            i += 2
        else:
            out.append(p)
            i += 1
    return out


def subsection_links(toc_html: str) -> list[tuple[str, str | None]]:
    """For a kāṇḍa TOC page (rows linking to leaf sub-section pages), return the
    ordered [(leaf-filename, heading-text)] pairs. The heading is the sub-section
    topic (used as `section` when the leaf page itself lacks a title row)."""
    m = re.search(r'wmsect[^>]*>(.*?)(?:<table\s+width="100%"|<div id="ftr")', toc_html, re.S | re.I)
    body = m.group(1) if m else toc_html
    out: list[tuple[str, str | None]] = []
    seen: set[str] = set()
    for href, txt in re.findall(r'<a\s+href="([^"]+)"[^>]*>(.*?)</a>', body, re.S | re.I):
        b = href.split("#")[0]
        if b.endswith(".html") and "/" not in b and b != "index.html" and b not in seen:
            seen.add(b)
            out.append((b, _clean(re.sub(r"<[^>]+>", "", txt)) or None))
    return out


def grouped_index_links(index_html: str) -> list[tuple[str, str | None, str | None]]:
    """For a single index that groups leaf links under #eedddd chapter headers
    (e.g. మనుచరిత్ర: ఆశ్వాసము headers + manuNNN.html sub-section links), return
    ordered [(leaf-filename, chapter, heading)] tracking the current header."""
    m = re.search(r'wmsect[^>]*>(.*?)(?:<div id="ftr"|</body>)', index_html, re.S | re.I)
    body = m.group(1) if m else index_html
    out: list[tuple[str, str | None, str | None]] = []
    chapter: str | None = None
    for tr_open, row in re.findall(r"(<tr[^>]*>)(.*?)</tr>", body, re.S | re.I):
        # TOC pages carry bgcolor on the <td>, not the <tr> — scan the whole row
        bg = (re.search(r"bgcolor=['\"]?#?([0-9a-f]{6})", tr_open + row) or [None, ""])[1].lower()
        if bg == "eedddd":
            cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S | re.I)
            t = _clean(re.sub(r"<[^>]+>", "", cells[0])) if cells else ""
            if t:
                chapter = t
            continue
        if bg in ("ffffcc", "eeeecc"):
            lk = re.search(r'<a\s+href="([^"]+)"[^>]*>(.*?)</a>', row, re.S | re.I)
            if lk:
                href = lk.group(1).split("#")[0]
                if href.endswith(".html") and "/" not in href and href != "index.html":
                    heading = _clean(re.sub(r"<[^>]+>", "", lk.group(2))) or None
                    out.append((href, chapter, heading))
    return out


def chapter_list(index_html: str) -> list[tuple[str, str]]:
    """Return [(href, chapter-name)] for the main content pages. Chapter pages
    are exactly N.html (section anchors carry a #fragment). Names may be plain
    (ప్రథమాశ్వాసము) or numbered (1. అవతారిక) — strip a leading "N. " prefix.
    De-dupes while preserving order."""
    out, seen = [], set()
    for href, txt in re.findall(r'<a\s+href="([^"]+)"[^>]*>(.*?)</a>', index_html, re.S | re.I):
        if not re.fullmatch(r"\d+\.html", href) or href in seen:
            continue
        name = _clean(re.sub(r"<[^>]+>", "", txt))
        name = re.sub(r"^\d+\.\s*", "", name)  # drop leading "1. " ordinal
        if name:
            seen.add(href)
            out.append((href, name))
    return out


def crawl_work(cfg: dict) -> None:
    base = f"{SITE}/{cfg['path']}"
    print(f"\n########## {cfg['title']} ({cfg['author']}) ##########")
    all_poems: list[dict] = []
    parse = parse_chapter_flexible if cfg.get("flexible") else parse_chapter

    if cfg.get("single_page"):
        # Whole work lives on index.html — fetch once and parse with the
        # selected parser. Each verse rolls up under chapter == work title.
        all_poems.extend(parse(fetch(f"{base}/index.html"), cfg["title"]))
        all_poems = [{"id": i, **p} for i, p in enumerate(all_poems, 1)]
        _write_work(cfg, base, all_poems)
        return

    if cfg.get("grouped_index"):
        # a single index groups leaf links under #eedddd ఆశ్వాసము headers
        links = grouped_index_links(fetch(f"{base}/index.html"))
        chaps = list(dict.fromkeys(c for _, c, _ in links))
        print(f"grouped index: {len(links)} leaves across {len(chaps)} chapters: {chaps}")
        for i, (leaf, chapter, heading) in enumerate(links):
            all_poems.extend(parse_chapter(fetch(f"{base}/{leaf}"), chapter, heading))
            time.sleep(0.4)
            if (i + 1) % 20 == 0:
                print(f"  ...{i + 1}/{len(links)} leaves, {len(all_poems)} padyalu")
        all_poems = [{"id": i, **p} for i, p in enumerate(all_poems, 1)]
        _write_work(cfg, base, all_poems)
        return

    if cfg.get("pages"):
        chapters = cfg["pages"]  # explicit (filename, chapter-name) list
    else:
        chapters = chapter_list(fetch(f"{base}/index.html"))
    print("chapters:", [n for _, n in chapters])
    for href, name in chapters:
        if cfg.get("subpages"):
            # `href` may be a TOC of leaf verse pages, OR a direct content page
            # (e.g. పీఠిక), OR a TOC whose links are missing. Auto-detect.
            page = fetch(f"{base}/{href}")
            time.sleep(0.4)
            ch_poems: list[dict] = parse_chapter(page, name)
            if ch_poems:
                # the page itself holds verses (e.g. పీఠిక) — a "next" nav link
                # must not be mistaken for a TOC, so check direct content first
                note = "direct content page"
            elif (leafs := subsection_links(page)):
                # each TOC also links the previous section's last leaf (a "prev"
                # nav link); keep only leaves of *this* page to avoid duplicates
                prefix = href[:-5]
                leafs = [(lf, hd) for lf, hd in leafs if lf.startswith(prefix) and lf != href]
                for leaf, heading in leafs:
                    ch_poems.extend(parse_chapter(fetch(f"{base}/{leaf}"), name, heading))
                    time.sleep(0.4)
                note = f"{len(leafs)} sub-pages"
            else:
                # broken/empty TOC — probe sequential leaves {prefix}NN.html
                prefix, n = href[:-5], 1
                while True:
                    leaf_page = fetch_optional(f"{base}/{prefix}{n:02d}.html")
                    if leaf_page is None:
                        break
                    ch_poems.extend(parse_chapter(leaf_page, name))
                    n += 1
                    time.sleep(0.4)
                note = f"{n - 1} sub-pages (probed; TOC empty)"
            print(f"  {href} ({name}): {note}, {len(ch_poems)} padyalu")
        else:
            ch_poems = parse_chapter(fetch(f"{base}/{href}"), name)
            print(f"  {href} ({name}): {len(ch_poems)} padyalu")
        all_poems.extend(ch_poems)
        time.sleep(0.6)
    all_poems = [{"id": i, **p} for i, p in enumerate(all_poems, 1)]
    _write_work(cfg, base, all_poems)


def _write_work(cfg: dict, base: str, all_poems: list[dict]) -> None:
    rec = {
        "shatakam_title_telugu": cfg["title"],
        "author_telugu": cfg["author"],
        "year": "unknown",
        "literary_form_telugu": cfg.get("form", "ఛందోగ్రంథము"),
        "source_url": f"{base}/index.html",
        "poems": all_poems,
    }
    OUT.mkdir(exist_ok=True)
    fp = OUT / f"{cfg['slug']}.json"
    fp.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  -> {fp.name} ({len(all_poems)} padyalu)")


def main() -> None:
    import sys
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for cfg in WORKS:
        if only and only not in (cfg["slug"], cfg["path"]):
            continue
        crawl_work(cfg)
    if _unmapped:
        print("\nmeter labels kept verbatim (not in abbrev map):", len(_unmapped))


if __name__ == "__main__":
    main()
