#!/usr/bin/env python3
"""Convert the crawled Wikisource kāvya texts into padyarchana-compatible JSON.

Output shape matches what scripts/import_json.py consumes:

    {
      "shatakam_title_telugu": <work title>,
      "author_telugu": <poet | "unknown">,
      "year": <year | "unknown">,
      "literary_form_telugu": <form>,
      "source_url": <wikisource url>,
      "poems": [
        {
          "id": <sequential, per work>,
          "padyam_number": <printed verse number | "unknown">,
          "lines_telugu": [ ...verse padams... ],
          "Chandassu": <meter inferred from the line-initial marker>,
          "chapter": <ఆశ్వాసము name>            # only for multi-canto works
          "makutam_telugu": <refrain>            # only for śatakaṃ works
          "bhavam": <prose meaning>,             # only where the source gives it
          "prathipadartham": null                # word-by-word gloss: not available
        }, ...
      ]
    }

Verses are split on the standard Telugu padya-lakṣaṇa markers that begin a line
(సీ. చ. క. ఉ. మ. తే. …); a సీసము is merged with the తే./గీ./ఆ. that concludes it.
Fields we cannot determine are filled with "unknown" (scalar metadata) or null
(prathipadartham / bhavam content), so nothing fake leaks into search/titles.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "json"
OUT_DIR.mkdir(exist_ok=True)

# line-initial abbreviation -> meter (chandassu) name.  Multi-char keys first.
MARKERS: dict[str, str] = {
    "శ్లో": "శ్లోకము",
    "గద్య": "గద్యము",
    "ద్విపద": "ద్విపద",
    "మత్త": "మత్తకోకిల",
    "తరల": "తరలము",
    "వృ": "వృత్తము",
    "సీ": "సీసము",
    "ఆ": "ఆటవెలది",
    "తే": "తేటగీతి",
    "గీ": "గీతము",
    "మా": "మాలిని",
    "శా": "శార్దూలవిక్రీడితము",
    "క": "కందము",
    "చ": "చంపకమాల",
    "ఉ": "ఉత్పలమాల",
    "మ": "మత్తేభవిక్రీడితము",
    "వ": "వచనము",
}
# the gīta-type meters that conclude a సీసము and merge into it
GITA = {"తే", "గీ", "ఆ"}
# prose meters that legitimately span long / multiple paragraphs
PROSE = {"వ", "గద్య"}
# a line this long is a whole stanza/paragraph, never a single padam of a verse
LONG_LINE = 95

# alternation ordered longest-first so శ్లో beats శా etc.
_MARK_ALT = "|".join(sorted((re.escape(k) for k in MARKERS), key=len, reverse=True))
_MARK_RE = re.compile(rf"^({_MARK_ALT})(?:\.|॥)\s*(.*)$")
_NUM_LINE = re.compile(r"^[|॥।\s]*\d+[|॥।\s]*$")
# a printed verse number at the end of the last line: " 15", "॥2॥", "||2||"
_TRAIL_NUM = re.compile(r"(?:\s+|[|॥।])\s*(\d+)\s*[|॥।]*\s*$")
_NOISE = re.compile(r"^(=+|-+|\[పుట\s*\d+\]|\.{3,})\s*$")
# editorial variant-reading footnotes, e.g. "… చూచు కాంక్షచే [మూ.]"
_FOOTNOTE = re.compile(r"\[మూ\.?\]")


def _marker(line: str):
    m = _MARK_RE.match(line)
    if not m:
        return None
    marker, rest = m.group(1), m.group(2).strip()
    # the source sometimes stacks the gīta abbreviation on the sīsa-concluding
    # line, e.g. "తే. గీ. …" — keep the first meter, drop the redundant గీ./తే./ఆ.
    m2 = _MARK_RE.match(rest)
    if m2 and m2.group(1) in GITA:
        rest = m2.group(2).strip()
    return marker, rest


class _Verse:
    __slots__ = ("marker", "chandassu", "lines", "number", "bhavam", "merged")

    def __init__(self, marker: str | None, first: str):
        self.marker = marker
        self.chandassu = MARKERS.get(marker, "unknown") if marker else "unknown"
        self.lines: list[str] = [first] if first else []
        self.number = None
        self.bhavam: list[str] = []
        self.merged = False


def parse_padyalu(text: str, *, chapter_names: set[str] | None = None,
                  start_after_first_chapter: bool = False,
                  capture_bhavam: bool = False,
                  fixed_chapter: str | None = None,
                  emit_unmarked: bool = False) -> list[dict]:
    chapter_names = chapter_names or set()
    chapter = fixed_chapter
    started = not start_after_first_chapter
    verses: list[_Verse] = []
    chapter_of: list[str | None] = []
    cur: _Verse | None = None
    in_bhavam = False

    def flush():
        nonlocal cur, in_bhavam
        if cur is not None:
            # strip a trailing printed number off the last verse line
            if cur.lines and cur.number is None:
                mt = _TRAIL_NUM.search(cur.lines[-1])
                if mt:
                    cur.lines[-1] = cur.lines[-1][: mt.start()].rstrip()
                    cur.number = int(mt.group(1))
            cur.lines = [ln for ln in cur.lines if ln.strip()]
            if cur.lines:
                verses.append(cur)
                chapter_of.append(chapter)
        cur = None
        in_bhavam = False

    for raw in text.split("\n"):
        line = raw.strip()
        if not line or _NOISE.match(line) or _FOOTNOTE.search(line):
            continue
        # chapter (ఆశ్వాసము) header — exact match only
        if line in chapter_names:
            flush()
            chapter = line
            started = True
            continue
        if not started:
            continue
        # start of a bhāvaṃ (prose-meaning) section
        if capture_bhavam and line.startswith("భావం"):
            in_bhavam = True
            continue
        mk = _marker(line)
        if mk:
            marker, first = mk
            in_bhavam = False  # a new verse marker closes any bhāvaṃ section
            # merge సీసము with its concluding గీత (తే./గీ./ఆ.)
            if cur is not None and cur.marker == "సీ" and not cur.merged \
                    and marker in GITA and cur.number is None:
                cur.merged = True
                cur.chandassu = "సీసము"
                if first:
                    cur.lines.append(first)
                continue
            flush()
            cur = _Verse(marker, first)
            continue
        # standalone printed verse number -> belongs to the verse just closed
        if _NUM_LINE.match(line):
            if not in_bhavam and cur is not None and cur.number is None:
                cur.number = int(line)
            continue
        if in_bhavam:
            if cur is not None:
                cur.bhavam.append(line)
            continue
        # --- a non-marker, non-number line ---
        # prose verses (వచనము/గద్యము) absorb everything until the next marker
        if cur is not None and cur.marker in PROSE and cur.number is None:
            cur.lines.append(line)
            continue
        if len(line) >= LONG_LINE:
            # a full paragraph/stanza — not a single padam of a metrical verse.
            # Emit it as its own padyam only for paragraph-rendered works (e.g.
            # ఆంధ్ర కామాయని) and only mid an *unnumbered* verse run. Otherwise it
            # is between-verse prose / a descriptive header / front matter / a
            # footnote block — skip it.
            emit = emit_unmarked and cur is not None and cur.number is None
            flush()
            if emit:
                cur = _Verse(None, line)  # meter unknown without a marker
            continue
        # a short line: a continuation padam of the current verse
        if cur is not None and cur.number is None:
            cur.lines.append(line)
    flush()

    out: list[dict] = []
    for i, (v, ch) in enumerate(zip(verses, chapter_of), 1):
        rec: dict = {
            "id": i,
            "padyam_number": v.number if v.number is not None else "unknown",
            "lines_telugu": v.lines,
            "Chandassu": v.chandassu,
        }
        if ch:
            rec["chapter"] = ch
        rec["bhavam"] = " ".join(v.bhavam).strip() if v.bhavam else None
        rec["prathipadartham"] = None
        out.append(rec)
    return out


WIKI = "https://te.wikisource.org/wiki/"

# per-work configuration -------------------------------------------------------
ASV4 = {"ప్రథమాశ్వాసము", "ద్వితీయాశ్వాసము", "తృతీయాశ్వాసము", "చతుర్థాశ్వాసము"}

SINGLE_FILE_WORKS = [
    dict(slug="srungaramaruka_kavyam", file="srungaramaruka_kavyam_full.txt",
         title="శృంగారామరుకావ్యము", author="తాళ్ళపాక తిరువేంగళప్ప", year="unknown",
         form="కావ్యము", url=WIKI + "శృంగారామరుకావ్యము"),
    dict(slug="tarikonda_nrusimha_satakam", file="tarikonda_nrusimha_satakam.txt",
         title="తరికొండ నృసింహశతకము", author="తరిగొండ వేంగమాంబ", year=2007,
         form="శతకము", url=WIKI + "తరికొండ నృసింహశతకము",
         capture_bhavam=True, makutam="తరిగొండ నృసింహ! దయాపయోనిధీ!"),
    dict(slug="srungaravrutta_padyalu_pedatirumalayya",
         file="srungaravrutta_padyalu_pedatirumalayya_full.txt",
         title="శృంగార వృత్తపద్యాల శతకము", author="తాళ్ళపాక పెదతిరుమలాచార్యులు",
         year="unknown", form="శతకము",
         url=WIKI + "పుట:శృంగారవృత్త పద్యాలు శ్రీ తాళ్ళపాక పెదతిరుమలయ్య.pdf/1"),
    dict(slug="andhra_kamayani_vavilala_somayajulu",
         file="andhra_kamayani_vavilala_somayajulu.txt",
         title="ఆంధ్ర కామాయని", author="వావిలాల సోమయాజులు", year=2018,
         form="కావ్యము", url=WIKI + "వావిలాల సోమయాజులు సాహిత్యం-1/ఆంధ్ర కామాయని",
         emit_unmarked=True),  # modern poetry: stanzas rendered as paragraphs
    dict(slug="shishupalavadha_mahakavyam", file="shishupalavadha_mahakavyam_full.txt",
         title="శిశుపాలవధ మహాకావ్యము", author="గోపినాథ వేంకటకవి", year=1975,
         form="మహాకావ్యము", url=WIKI + "శిశుపాలవధ",
         chapters=ASV4, start_after_first_chapter=True),
]

# multi-canto works crawled into one file per ఆశ్వాసము
CHAPTER_WORKS = [
    dict(slug="radhikasantvanamu", title="రాధికాసాంత్వనము", author="ముద్దుపళని",
         year=1953, form="శృంగారకావ్యప్రబంధము",
         url=WIKI + "రాధికాసాంత్వనము (ముద్దుపళని)",
         files=[("radhikasantvanamu_01_01_prathamaswasamu.txt", "ప్రథమాశ్వాసము"),
                ("radhikasantvanamu_02_02_dvitiyaswasamu.txt", "ద్వితీయాశ్వాసము"),
                ("radhikasantvanamu_03_03_trutiyaswasamu.txt", "తృతీయాశ్వాసము"),
                ("radhikasantvanamu_04_04_chaturthaswasamu.txt", "చతుర్థాశ్వాసము")]),
    dict(slug="dhanurvidyavilasamu", title="ధనుర్విద్యావిలాసము",
         author="కృష్ణమాచార్యుఁడు", year=1950, form="కావ్యము",
         url=WIKI + "ధనుర్విద్యావిలాసము",
         files=[("dhanurvidyavilasamu_01_01_prathamaswasamu.txt", "ప్రథమాశ్వాసము"),
                ("dhanurvidyavilasamu_02_02_dvitiyaswasamu.txt", "ద్వితీయాశ్వాసము"),
                ("dhanurvidyavilasamu_03_03_trutiyaswasamu.txt", "తృతీయాశ్వాసము")]),
    dict(slug="talankanandiniparinayamu", title="తాలాంకనందినీపరిణయము",
         author="ఆసూరి మఱింగంటి వేంకట నరసింహాచార్యులు", year=1980, form="ప్రబంధము",
         url=WIKI + "తాలాంకనందినీపరిణయము",
         files=[("talankanandiniparinayamu_01_01_prathamaswasamu.txt", "ప్రథమాశ్వాసము"),
                ("talankanandiniparinayamu_02_02_dvitiyaswasamu.txt", "ద్వితీయాశ్వాసము"),
                ("talankanandiniparinayamu_03_03_trutiyaswasamu.txt", "తృతీయాశ్వాసము"),
                ("talankanandiniparinayamu_04_04_chaturthaswasamu.txt", "చతుర్థాశ్వాసము"),
                ("talankanandiniparinayamu_05_05_panchamaswasamu.txt", "పంచమాశ్వాసము"),
                ("talankanandiniparinayamu_06_06_shashthaswasamu.txt", "షష్ఠాశ్వాసము")]),
    dict(slug="ahalyasankrandanamu", title="అహల్యాసంక్రందనము",
         author="సముఖము వేంకట కృష్ణప్ప నాయకుడు", year=1901, form="ప్రబంధము",
         url=WIKI + "అహల్యాసంక్రందనము",
         files=[("ahalyasankrandanamu_01_01_prathamaswasamu.txt", "ప్రథమాశ్వాసము"),
                ("ahalyasankrandanamu_02_02_dvitiyaswasamu.txt", "ద్వితీయాశ్వాసము"),
                ("ahalyasankrandanamu_03_03_trutiyaswasamu.txt", "తృతీయాశ్వాసము")]),
    dict(slug="chandrika_parinayamu", title="చంద్రికా పరిణయము",
         author="సురభి మాధవ రాయలు", year=1982, form="ప్రబంధము",
         url=WIKI + "చంద్రికా పరిణయము",
         files=[("chandrika_parinayamu_01_01_prathamaswasamu.txt", "ప్రథమాశ్వాసము"),
                ("chandrika_parinayamu_02_02_dvitiyaswasamu.txt", "ద్వితీయాశ్వాసము"),
                ("chandrika_parinayamu_03_03_trutiyaswasamu.txt", "తృతీయాశ్వాసము"),
                ("chandrika_parinayamu_04_04_chaturthaswasamu.txt", "చతుర్థాశ్వాసము"),
                ("chandrika_parinayamu_05_05_panchamaswasamu.txt", "పంచమాశ్వాసము"),
                ("chandrika_parinayamu_06_06_shashthaswasamu.txt", "షష్ఠాశ్వాసము")]),
    dict(slug="gopinatha_ramayanamu", title="గోపీనాథ రామాయణము",
         author="గోపీనాథము వేంకటకవి", year=1923, form="మహాకావ్యము",
         url=WIKI + "గోపీనాథ రామాయణము",
         files=[("gopinatha_ramayanamu_01_00_pithika.txt", "పీఠిక"),
                ("gopinatha_ramayanamu_02_01_balakandamu.txt", "బాలకాండము"),
                ("gopinatha_ramayanamu_03_02_ayodhyakandamu.txt", "అయోధ్యాకాండము"),
                ("gopinatha_ramayanamu_04_03_ayodhyakandamu_contd.txt", "అయోధ్యాకాండము (కొనసాగింపు)"),
                ("gopinatha_ramayanamu_05_04_aranyakandamu.txt", "ఆరణ్యకాండము")]),
    dict(slug="prabandharaja_venkateswara_vijaya_vilasamu",
         title="శ్రీ ప్రబంధరాజ వేంకటేశ్వర విజయ విలాసము",
         author="గణపవరపు వెంకటకవి", year=1977, form="ప్రబంధము",
         url=WIKI + "శ్రీ ప్రబంధరాజ వేంకటేశ్వర విజయ విలాసము",
         files=[("prabandharaja_venkateswara_vijaya_vilasamu_01_01_avatarika.txt", "అవతారిక"),
                ("prabandharaja_venkateswara_vijaya_vilasamu_02_02_ekaswasamu.txt", "ఏకాశ్వాసము")]),
    dict(slug="sivaratri_mahatmyamu", title="శివరాత్రిమాహాత్మ్యము",
         author="శ్రీనాథుడు", year="unknown", form="ప్రబంధము",
         url=WIKI + "శివరాత్రిమాహాత్మ్యము",
         files=[("sivaratri_mahatmyamu_01_01_prathamaswasamu.txt", "ప్రథమాశ్వాసము"),
                ("sivaratri_mahatmyamu_02_02_dvitiyaswasamu.txt", "ద్వితీయాశ్వాసము"),
                ("sivaratri_mahatmyamu_03_03_trutiyaswasamu.txt", "తృతీయాశ్వాసము"),
                ("sivaratri_mahatmyamu_04_04_chaturthaswasamu.txt", "చతుర్థాశ్వాసము"),
                ("sivaratri_mahatmyamu_05_05_panchamaswasamu.txt", "పంచమాశ్వాసము")]),
]


def _strip_header(text: str) -> str:
    """Drop the leading === banner block we wrote into each crawl file."""
    lines = text.split("\n")
    # skip an initial ===...=== title block
    if lines and lines[0].startswith("="):
        for i in range(1, len(lines)):
            if lines[i].startswith("=") and i > 1:
                return "\n".join(lines[i + 1:])
    return text


def build_record(cfg: dict, poems: list[dict]) -> dict:
    rec = {
        "shatakam_title_telugu": cfg["title"],
        "author_telugu": cfg.get("author") or "unknown",
        "year": cfg.get("year", "unknown"),
        "literary_form_telugu": cfg["form"],
        "source_url": cfg["url"],
        "poems": poems,
    }
    if cfg.get("makutam"):
        for p in poems:
            p["makutam_telugu"] = cfg["makutam"]
    return rec


def main() -> None:
    summary = []
    for cfg in SINGLE_FILE_WORKS:
        text = _strip_header((HERE / cfg["file"]).read_text(encoding="utf-8"))
        poems = parse_padyalu(
            text,
            chapter_names=cfg.get("chapters"),
            start_after_first_chapter=cfg.get("start_after_first_chapter", False),
            capture_bhavam=cfg.get("capture_bhavam", False),
            emit_unmarked=cfg.get("emit_unmarked", False),
        )
        rec = build_record(cfg, poems)
        out = OUT_DIR / f"{cfg['slug']}.json"
        out.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
        summary.append((cfg["slug"], len(poems)))
        print(f"  {out.name}: {len(poems)} padyalu")

    for cfg in CHAPTER_WORKS:
        all_poems: list[dict] = []
        for fname, asv in cfg["files"]:
            text = _strip_header((HERE / fname).read_text(encoding="utf-8"))
            all_poems.extend(parse_padyalu(text, fixed_chapter=asv))
        for i, p in enumerate(all_poems, 1):
            p["id"] = i
        rec = build_record(cfg, all_poems)
        out = OUT_DIR / f"{cfg['slug']}.json"
        out.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
        summary.append((cfg["slug"], len(all_poems)))
        print(f"  {out.name}: {len(all_poems)} padyalu")

    print("\nTotal padyalu:", sum(n for _, n in summary))


if __name__ == "__main__":
    main()
