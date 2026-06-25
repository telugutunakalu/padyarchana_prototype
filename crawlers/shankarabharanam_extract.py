#!/usr/bin/env python3
"""Phase 2 (v1) — extract padyalu from the శంకరాభరణం raw comment dump.

Each comment is authored by a poet (the commenter). We:
  * drop deleted comments and pure praise/chatter / host-feedback;
  * strip the surrounding metadata lines (date, పద్య సంఖ్య, స.క.స number, the
    restated సమస్య, "పూరణము :--" headers, glossary `word=meaning` lines,
    name/location signatures);
  * capture the self-declared meter (పూరణము :-- X, or a line-initial abbrev
    like ఉ: చ: క: శా: మ: తే: ఆ: సీ:) when present;
  * keep the remaining verse lines as one padyam, attributed to the commenter,
    tagged category "online padyalu" with the post (challenge) as context.

This is a tunable first pass — run with `--sample N` to inspect quality.
"""
from __future__ import annotations

import argparse
import glob
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "crawlers" / "shankarabharanam_raw" / "posts"
HOST = "కంది శంకరయ్య"

ABBR = {
    "ఉ": "ఉత్పలమాల", "చ": "చంపకమాల", "చం": "చంపకమాల", "మ": "మత్తేభవిక్రీడితము",
    "శా": "శార్దూలవిక్రీడితము", "క": "కందము", "కం": "కందము", "తే": "తేటగీతి",
    "ఆ": "ఆటవెలది", "సీ": "సీసము", "గీ": "గీతము", "వ": "వచనము", "మత్త": "మత్తకోకిల",
}
_METER_NAMES = ("ఉత్పలమాల చంపకమాల మత్తేభవిక్రీడితము శార్దూలవిక్రీడితము కందము తేటగీతి "
                "ఆటవెలది సీసము గీతము వచనము మత్తకోకిల ద్విపద కంద మాలిని స్రగ్ధర").split()
_DECL = re.compile(r"పూరణ\w*\s*[:\-–=]+\s*([^\n,.]{2,20})")
_ABBR_LINE = re.compile(r"^\s*([ఉచకశామతేఆసీగీవం]{1,3})\s*[:.\-–)]\s*(.*)$")

_DELETED = re.compile(r"తీసివేశ|removed by")
# metadata / signature lines to strip from inside a comment
_META = re.compile(
    r"పద్య\s*సంఖ్య|స\.?\s*క\.?\s*స\.?|శంకరాభరణం\s*వార|సమస్య\s*[:\-–]|దత్తపది\s*[:\-–]"
    r"|పూరణ\w*\s*[:\-–=]|^\d+[-/]\d+[-/]\d+|^\s*\d+\s*$|గారి?కి|^[\w\s]*నమస్కార"
    r"|^\s*\*+\s*$|హైదరాబాద|విశాఖ|గుంటూ|విజయవాడ|వరంగల్|^\W*$|^[ఀ-౿]+\s*ఉవాచ")
# prose / discussion / praise markers → a verse block carrying any of these is
# feedback or commentary, NOT a clean padya submission (precision-first → drop).
_PROSE = re.compile(
    r"పరిశీలించ|అనుమాన|సందేహ|విజ్ఞులు|గమనించ|తెలుపగలర|సవరించ|అనుకుంటు|అభిప్రాయ"
    r"|వివరించ|సరిచేయ|క్షమించ|నమస్కార|ధన్యవాద|అభినందన|బాగుంది|బాగున్న|మనోహరం?గ"
    r"|చక్కగ|నచ్చింది|హృద్యం|రసవత్|=>|http|@|గారూ|గారు\b|అండి\b|\bకదా\b")
_TEL = re.compile(r"[ఀ-౿]")
_GLOSS = re.compile(r"\S+\s*=\s*\S+")          # word=meaning glossary line

_METER_FIX = {
    "కంద": "కందము", "కం": "కందము", "క": "కందము", "ఉ": "ఉత్పలమాల", "చ": "చంపకమాల",
    "చం": "చంపకమాల", "మ": "మత్తేభవిక్రీడితము", "శా": "శార్దూలవిక్రీడితము",
    "తే": "తేటగీతి", "ఆ": "ఆటవెలది", "సీ": "సీసము", "గీ": "గీతము", "వ": "వచనము",
    "తే.గీ": "తేటగీతి", "ఆ.వె": "ఆటవెలది",
}


def norm_meter(m: str | None) -> str:
    if not m:
        return "unknown"
    return _METER_FIX.get(m.strip(), m.strip())


_KEEP = re.compile(r"[^ఀ-౿\s.,;:!\"'()\-–—|॥।ఁ]")   # emoji / latin / symbol noise
_LATIN = re.compile(r"[A-Za-z]")
_EMO = re.compile(r":\)|:-\)|:D|:\(|;\)|😀|🙏|👇|😊|☺")
# leading heading / greeting / label lines that precede a verse
_HEADER = re.compile(r"పూరణ|నమస్సుల|నమః|గురుభ్యో|శుభ|మనవి|సందర్భ|మైలవరపు|వారి\b|ఉవాచ"
                     r"|స్వీకరించ|పద్యము?\s*$|చిత్ర\w*నువైన|విలసితము")
# feedback / critique / praise vocabulary → a block carrying these is not a pūraṇa
_FEEDBACK = re.compile(r"బాగా|బాగు|అద్భుత|మంచి\b|అన్వయ|ప్రశంస|దోష\b|సవరణ|విరుపు|సముచిత"
                       r"|ధన్యవాద|అభినందన|శుభాకాంక్ష|చక్క|మనోహర|రసవత్|హృద్యం|నచ్చ|క్షమించ"
                       r"|baagu|dhany|abhinand|nunna|chala|చూద్దాము|చూద్దాం|గలరా|గలరు\b"
                       r"|లేవా|వినూత్న|పూరణలు")
# byline / attribution header (someone-else's పూరణ, a śatakam citation, ఉవాచ) —
# strip from the TOP of a block unconditionally (very unlikely inside a verse).
_BYLINE = re.compile(r"పూరణ\s*$|పూరణము\s*$|ఉవాచ|శతకము\s+నుండి|గారి.*పూరణ|వారి\s+పూరణ"
                     r"|(వారు|గారు|గారి)\s*చెప్పిన|చెప్పినట్లు|వారన్నట్లు|సూచన\s*మేరకు")
# honorific-prefixed bare byline line (a poet credit, never the start of a verse)
_LEADBYLINE = re.compile(r"^(డా\.?|డాక్టర్|శ్రీమతి|ప్రొ\.?|కీ\.?\s*శే\.?|శ్రీయుత)\b")
# the challenge PROMPT itself (instructions), not an answer verse
_PROMPT = re.compile(r"వ్రాయండి|వ్రాయుము|పూరించండి|పూరించుము|సందర్భము\s*[:：]"
                     r"|ఛందస్సు\s*[-–:]|నిషిద్ధము|మీ\s+ఇష్టము|గమనిక\s*[:：]|గణాలు"
                     r"|\b[ఀ-౿]+-[ఀ-౿]+-[ఀ-౿]+-[ఀ-౿]+\b")


def _midword_cut(ln: str) -> bool:
    """Last line ends on a 1–2 akshara fragment with no terminator → truncated."""
    toks = ln.split()
    if not toks:
        return True
    return len(toks[-1]) <= 2 and ln.rstrip()[-1:] not in "।॥.!,;\"'"


def clean_verse(ln: str) -> str:
    return re.sub(r"\s+", " ", _KEEP.sub("", ln)).strip()


def _latin_ratio(s: str) -> float:
    ns = [c for c in s if not c.isspace()]
    return len(_LATIN.findall(s)) / len(ns) if ns else 0.0


def _is_header(ln: str) -> bool:
    return bool(_HEADER.search(ln)) or ln.rstrip().endswith((":", "-", "–", "："))


def _is_signature(ln: str) -> bool:
    if _EMO.search(ln) or _latin_ratio(ln) > 0.35:
        return True
    # short trailing name line: ≤3 tokens, ends with '.', no internal comma/danda
    return (len(ln) < 28 and ln.rstrip().endswith(".") and "," not in ln
            and "॥" not in ln and len(ln.split()) <= 3)


def _line_is_verse(ln: str) -> bool:
    if not (10 <= len(ln) <= 78):
        return False
    if _GLOSS.match(ln) or _META.search(ln) or _PROSE.search(ln) or _EMO.search(ln):
        return False
    if ln.count(".") > 2 or "?" in ln or "=>" in ln or _latin_ratio(ln) > 0.35:
        return False
    return _tel_ratio(ln) >= 0.7


def _norm(s: str) -> str:
    return re.sub(r"[^ఀ-౿a-zA-Z]", "", s).lower()


def _is_author_sig(ln: str, author_n: str) -> bool:
    """The signature line is almost always the commenter's own name."""
    if not author_n:
        return False
    n = _norm(ln)
    return bool(n) and (n == author_n or (len(n) >= 6 and (n in author_n or author_n in n)))


def clean_html(h: str) -> str:
    h = re.sub(r"<br\s*/?>", "\n", h)
    h = re.sub(r"</p>|</div>", "\n", h)
    h = re.sub(r"<[^>]+>", "", h)
    return html.unescape(h)


def _tel_ratio(s: str) -> float:
    ns = [c for c in s if not c.isspace()]
    return len(_TEL.findall(s)) / len(ns) if ns else 0.0


def detect_meter(text: str, lines: list[str]) -> str | None:
    m = _DECL.search(text)
    if m:
        for nm in _METER_NAMES:
            if nm[:4] in m.group(1):
                return nm
    for ln in lines[:3]:
        a = _ABBR_LINE.match(ln)
        if a and a.group(1) in ABBR:
            return ABBR[a.group(1)]
    # a bare meter name or "(తేటగీతి)" within the first couple of lines
    for ln in lines[:2]:
        for nm in _METER_NAMES:
            if nm in ln and len(ln) <= len(nm) + 6:
                return nm
    return None


def _strip_abbrev(ln: str) -> str:
    a = _ABBR_LINE.match(ln)
    if a and a.group(1) in ABBR:
        return a.group(2).strip()
    return ln


def extract_from_comment(content_html: str, author: str = "") -> list[dict]:
    """Precision-first: isolate contiguous runs of clean verse lines (2–8),
    dropping all surrounding metadata/prose; reject any run that carries a
    discussion/praise marker or fails structural checks."""
    text = clean_html(content_html)
    if _DELETED.search(text):
        return []
    author_n = _norm(author)
    raw = [re.sub(r"\s+", " ", ln).strip() for ln in text.split("\n")]
    raw = [_strip_abbrev(ln) for ln in raw if ln.strip()]
    meter = norm_meter(detect_meter(text, raw))

    runs: list[list[str]] = []
    cur: list[str] = []
    for ln in raw:
        if _line_is_verse(ln):
            cur.append(ln)
        else:
            if len(cur) >= 2:
                runs.append(cur)
            cur = []
    if len(cur) >= 2:
        runs.append(cur)

    out: list[dict] = []
    for run in runs:
        run = [clean_verse(x) for x in run if len(clean_verse(x)) >= 8]
        # strip author-signature / byline / colon-header lines from both edges
        while run and (_BYLINE.search(run[0]) or _LEADBYLINE.match(run[0])
                       or run[0].rstrip().endswith((":", "："))
                       or _is_author_sig(run[0], author_n)):
            run = run[1:]
        while run and (_is_author_sig(run[-1], author_n) or _LEADBYLINE.match(run[-1])):
            run = run[:-1]
        # strip leading headers / trailing signatures down toward a valid form
        while len(run) > 4 and _is_header(run[0]):
            run = run[1:]
        while len(run) > 4 and _is_signature(run[-1]):
            run = run[:-1]
        if any(_FEEDBACK.search(x) or _PROMPT.search(x) for x in run):   # prose / prompt → drop
            continue
        is_sisa = meter == "సీసము"
        if is_sisa and 6 <= len(run) <= 8 and _valid_block(run):
            out.append({"lines_telugu": run, "Chandassu": meter})
        elif is_sisa:                                   # సీసము needs 6–8 lines → 4-line is cut
            continue
        elif len(run) == 4 and _valid_block(run):
            out.append({"lines_telugu": run, "Chandassu": meter})
        elif len(run) == 8:                             # merged 4+4 → two padyalu
            for half in (run[:4], run[4:]):
                if _valid_block(half):
                    out.append({"lines_telugu": half, "Chandassu": meter})
        # else (2,3,5,6,7,>8) → drop for precision
    return out


def _valid_block(lines: list[str]) -> bool:
    if not lines or any(_latin_ratio(x) > 0.3 for x in lines):
        return False
    if _midword_cut(lines[-1]):                 # final padam cut off mid-word
        return False
    # a complete padyam effectively never ends on a dangling arasunna (ఁ) — cut
    last = re.sub(r"[\s.,!;:\"'॥।\-–]+$", "", lines[-1])
    if last.endswith("ఁ"):
        return False
    L = [len(x) for x in lines]
    if sum(L) < 55:
        return False
    if max(L) > 3.3 * min(L) and min(L) < 14:
        return False
    return True


def process_post(d: dict) -> list[dict]:
    out = []
    for c in d.get("comments", []):
        for p in extract_from_comment(c.get("content_html", ""), c.get("author", "")):
            p.update({
                "poet": c.get("author", "").strip(),
                "published": c.get("published", "")[:10],
                "challenge": d.get("title", ""),
                "challenge_type": (d.get("labels") or ["?"])[0],
                "source_url": d.get("url"),
            })
            out.append(p)
    return out


OUT_FILE = ROOT / "crawlers" / "shankarabharanam_extracted.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0, help="process only N random posts (stats only)")
    ap.add_argument("--full", action="store_true", help="process all posts and write OUT_FILE")
    args = ap.parse_args()
    files = sorted(glob.glob(str(RAW / "*.json")))
    if args.sample:
        import random
        files = random.Random(11).sample(files, args.sample)
    total_comments = total_padya = 0
    by_meter: dict = {}
    by_type: dict = {}
    poets: set = set()
    examples = []
    all_padya = []
    for f in files:
        d = json.loads(Path(f).read_text())
        total_comments += len(d.get("comments", []))
        ps = process_post(d)
        total_padya += len(ps)
        for p in ps:
            by_meter[p["Chandassu"]] = by_meter.get(p["Chandassu"], 0) + 1
            by_type[p["challenge_type"]] = by_type.get(p["challenge_type"], 0) + 1
            poets.add(p["poet"])
        if args.full:
            all_padya.extend(ps)
        if ps and len(examples) < 12:
            examples.append(ps[0])
    print(f"posts: {len(files)} | comments: {total_comments} | extracted padyalu: {total_padya} "
          f"({100*total_padya/max(1,total_comments):.0f}% of comments) | distinct poets: {len(poets)}")
    print("by meter:", dict(sorted(by_meter.items(), key=lambda x: -x[1])))
    print("by challenge type:", dict(sorted(by_type.items(), key=lambda x: -x[1])[:8]))
    if args.full:
        for i, p in enumerate(all_padya, 1):
            p["id"] = i
        OUT_FILE.write_text(json.dumps(all_padya, ensure_ascii=False), encoding="utf-8")
        print(f"\n-> wrote {len(all_padya)} padyalu to {OUT_FILE}")
    else:
        print("\n=== examples ===")
        for e in examples[:8]:
            print(f"\n[{e['challenge_type']}] {e['poet']} | {e['Chandassu']} | {e['challenge']}")
            for ln in e["lines_telugu"][:6]:
                print("   ", ln[:64])


if __name__ == "__main__":
    main()
