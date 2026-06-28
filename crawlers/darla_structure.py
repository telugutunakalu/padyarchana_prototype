#!/usr/bin/env python3
"""Phase 2 — structure the దార్ల blog crawl (crawlers/darla_raw/) into
padyarchana-format JSON.

The blog mixes several padyam layouts across 8 years of posts:
  * clean day-posts: each padam in its own <p>; padyalu separated by a blank
    <p><br/></p>; 4-line ఆటవెలది/తేటగీతి.  (the majority)
  * "explained" posts: each padyam preceded by a standalone meter-marker line
    (తే.గీ. / కం. / ఆ.వె. / సీ.) and FOLLOWED by a "(భావం: …)" prose-meaning
    paragraph — no blank separators.
  * 2018 గణేష్-పత్రిక posts: <span>padam</span><br/> lines, double-<br/> between
    padyalu, sometimes only a newspaper image (no text).
  * prose / diary / newspaper-response / image-only posts: no padyalu → skipped.

Unified walker: a new padyam starts at EITHER a blank gap OR a meter-marker line;
a "(భావం…)" line attaches as bhavam; the leading post-title line and long prose
lines are dropped. Low-confidence extractions are flagged, not silently shipped.
Author = దార్ల వెంకటేశ్వరరావు for all (user decision); a per-poem note records
the original author where a post is someone else's padyam.
"""
from __future__ import annotations

import html
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "crawlers" / "darla_raw"
POSTS = RAW / "posts"

# ---- meter markers ---------------------------------------------------------
# దార్ల labels each padyam's meter either as a full name ("సీసము:", "తే.గీ:") or
# an abbreviation, EITHER on its own line ("కం.") OR as a prefix on the first
# padam ("సీ॥ కౌమారదశనుండి …").  We recognise both, infer the Chandassu, and the
# redundant గీ/తే/ఆ stacked on a సీస-గీత marker is folded away.

# full meter names (optional terminator, optional rest) — order longest-first
_NAMES = [
    ("సీసపద్యము", "సీసము"), ("సీసపద్యం", "సీసము"), ("సీసము", "సీసము"),
    ("తేటగీతి", "తేటగీతి"), ("ఆటవెలది", "ఆటవెలది"),
    ("కందపద్యము", "కందము"), ("కందపద్యం", "కందము"), ("కందము", "కందము"),
    ("మత్తేభవిక్రీడితము", "మత్తేభవిక్రీడితము"), ("మత్తేభము", "మత్తేభవిక్రీడితము"),
    ("మత్తేభం", "మత్తేభవిక్రీడితము"),
    ("శార్దూలవిక్రీడితము", "శార్దూలవిక్రీడితము"), ("శార్దూలము", "శార్దూలవిక్రీడితము"),
    ("చంపకమాల", "చంపకమాల"), ("ఉత్పలమాల", "ఉత్పలమాల"),
    ("మత్తకోకిల", "మత్తకోకిల"), ("ఉత్సాహము", "ఉత్సాహము"),
    ("మాలిని", "మాలిని"), ("స్రగ్ధర", "స్రగ్ధర"),
]
# abbreviations — regex fragment -> Chandassu (longest / most specific first)
_ABBR = [
    (r"తే\.?\s*గీ", "తేటగీతి"), (r"ఆ\.?\s*వె", "ఆటవెలది"),
    (r"మత్త", "మత్తకోకిల"), (r"ఉత్సాహ", "ఉత్సాహము"), (r"శ్లో", "శ్లోకము"),
    (r"సీ", "సీసము"), (r"తే", "తేటగీతి"), (r"గీ", "గీతము"), (r"ఆ", "ఆటవెలది"),
    (r"కం", "కందము"), (r"శా", "శార్దూలవిక్రీడితము"), (r"మ", "మత్తేభవిక్రీడితము"),
    (r"ఉ", "ఉత్పలమాల"), (r"చ", "చంపకమాల"), (r"వృ", "వృత్తము"), (r"క", "కందము"),
]
_TERM = r"[.:।॥|]"
_GITA = ("తే", "గీ", "ఆ")

# full-name alternation (escaped) keeping the input order
_NAME_ALT = "|".join(re.escape(n) for n, _ in _NAMES)
_ABBR_ALT = "|".join(p for p, _ in _ABBR)
_NAME_MAP = {n: m for n, m in _NAMES}

# standalone: whole line is just a name (term optional) -> declaration
_NAME_DECL = re.compile(rf"^\s*({_NAME_ALT})\s*{_TERM}*\s*$")
# inline: name + rest
_NAME_INLINE = re.compile(rf"^\s*({_NAME_ALT})\s*{_TERM}*\s*(\S.*)$")
# standalone abbreviation: whole line is just the abbr (term optional)
_ABBR_DECL = re.compile(rf"^\s*({_ABBR_ALT})\s*{_TERM}*\s*$")
# inline abbreviation: abbr + REQUIRED terminator + rest (so a real word that
# merely starts with క/మ/ఆ never matches)
_ABBR_INLINE = re.compile(rf"^\s*({_ABBR_ALT})\s*{_TERM}+\s*(\S.*)$")

_BHAVAM_RE = re.compile(r"^\s*[(\[]?\s*భావ(?:ం|ము|ార్థ)\s*[:ం]?", re.U)
_HEADING_RE = re.compile(r"^\s*\d+\s*[.)]\s+\S")          # "1. తీపి …" section head
_SIGN_RE = re.compile(r"^\s*[-–—‒]\s*\S")                  # "- దార్ల వెంకటేశ్వరరావు …"
_DATE_RE = re.compile(r"^\s*\d{1,2}[./]\d{1,2}[./]\d{2,4}\s*$")
_ELLIPSIS_RE = re.compile(r"^\s*[.…]{1,}\s*$")
# author signature / institutional affiliation lines that tail many posts
_SIG_RE = re.compile(
    r"దార్ల\s*వె[ీే]?ంకటేశ్వరరావు|యూనివర్సిటీ|సెంట్రల్\s*యూని|తెలుగు\s*శాఖ"
    r"|విశ్వవిద్యాల|హైదరాబా(?:దు|ద్)|సెంటర్\s*ఫర్", re.U)
# a line at/over this length is prose, never a single padam
LONG_LINE = 90


def _abbr_meter(token: str) -> str | None:
    for pat, name in _ABBR:
        if re.fullmatch(pat, token):
            return name
    return None


def match_marker(line: str):
    """Return (chandassu, rest) if `line` is/starts-with a meter marker, else
    None.  rest='' means a standalone marker line (meter applies to the NEXT
    padyam); rest non-empty means the marker prefixed the first padam."""
    for rx, inline in ((_NAME_DECL, False), (_NAME_INLINE, True)):
        m = rx.match(line)
        if m:
            meter = _NAME_MAP[m.group(1)]
            rest = (m.group(2).strip() if inline else "")
            return _fold_gita(meter, rest)
    for rx, inline in ((_ABBR_DECL, False), (_ABBR_INLINE, True)):
        m = rx.match(line)
        if m:
            meter = _abbr_meter(m.group(1))
            if meter is None:
                continue
            rest = (m.group(2).strip() if inline else "")
            return _fold_gita(meter, rest)
    return None


def _fold_gita(meter: str, rest: str):
    """A సీస-గీత line is sometimes written "తే. గీ. …" or "సీ॥ తే॥ …": drop a
    redundant leading గీత-abbreviation from `rest`."""
    if rest:
        m2 = _ABBR_INLINE.match(rest) or _ABBR_DECL.match(rest)
        if m2 and m2.group(1) in _GITA:
            rest = (m2.group(2).strip() if m2.lastindex and m2.lastindex >= 2 else "")
    return meter, rest


def html_to_lines(body: str) -> list[str]:
    """post-body HTML -> list of text lines, blanks preserved as separators.
    Block-aware: a block whose only content is <br>/empty becomes ONE blank
    line; <br> inside a content block becomes internal line breaks; adjacent
    </p><p> is a plain line break (no spurious blank)."""
    body = re.sub(r"<img[^>]*>", "", body, flags=re.I)
    body = re.sub(r"</(p|div|li|h[1-6]|tr|td|blockquote)\s*>", "\x00", body, flags=re.I)
    body = re.sub(r"<(p|div|li|h[1-6]|tr|td|blockquote)[^>]*>", "", body, flags=re.I)
    out: list[str] = []
    for blk in body.split("\x00"):
        parts = re.split(r"<br[^>]*>", blk, flags=re.I)
        sub = []
        for part in parts:
            t = re.sub(r"<[^>]+>", "", part)
            t = html.unescape(t)                       # &#3147; -> ఓ , &nbsp; -> \xa0
            t = unicodedata.normalize("NFC", t)
            # drop zero-width spaces / joiners / BOM that pad Word-pasted text,
            # and the asterisks some posts wrap meter markers in ("*ఆ.వె.*")
            t = (t.replace("\xa0", " ").replace("​", "").replace("‌", "")
                  .replace("‍", "").replace("﻿", "").replace("*", ""))
            t = re.sub(r"[ \t\r\n]+", " ", t).strip()
            sub.append(t)
        if all(p == "" for p in sub):
            out.append("")
        else:
            out.extend(sub)
    return out


def _norm_title(s: str) -> str:
    s = unicodedata.normalize("NFC", s or "")
    return re.sub(r"\s+", "", s.replace("​", "")).strip()


class Padyam:
    __slots__ = ("lines", "meter", "bhavam", "flag")

    def __init__(self, meter=None):
        self.lines: list[str] = []
        self.meter = meter
        self.bhavam: list[str] = []
        self.flag: str | None = None


def parse_post(body_html: str, post_title: str) -> tuple[list[Padyam], list[str]]:
    """Return (padyalu, dropped_prose_lines)."""
    lines = html_to_lines(body_html)
    title_norm = _norm_title(post_title)
    padyalu: list[Padyam] = []
    dropped: list[str] = []
    cur: Padyam | None = None
    pending_meter: str | None = None
    seen_title = False

    def flush():
        nonlocal cur
        if cur and cur.lines:
            padyalu.append(cur)
        cur = None

    for ln in lines:
        if ln == "":
            flush()
            continue
        # drop the leading title line (appears once, near the top)
        if not seen_title and _norm_title(ln) == title_norm and title_norm:
            seen_title = True
            continue
        # bhavam — check before the generic "(" / prose rules. A bhavam always
        # CONCLUDES its padyam, so attach then flush: this also separates the
        # otherwise-undelimited "kandam, bhavam, kandam, bhavam …" runs.
        if _BHAVAM_RE.match(ln):
            txt = re.sub(r"^\s*[(\[]?\s*భావ(?:ం|ము|ార్థ)\s*[:ం]?\s*", "", ln)
            txt = txt.rstrip(")].").strip()
            if cur:
                cur.bhavam.append(txt)
                flush()
            elif padyalu:
                padyalu[-1].bhavam.append(txt)
            continue
        # author signature / affiliation tail → end padyam, skip
        if len(ln) <= 60 and _SIG_RE.search(ln):
            flush()
            pending_meter = None
            continue
        mk = match_marker(ln)
        if mk:
            meter, rest = mk
            flush()
            if rest:                       # marker prefixed the first padam
                cur = Padyam(meter=meter)
                cur.lines.append(rest)
            else:                          # standalone marker → next padyam
                pending_meter = meter
            continue
        # separators that aren't padams: numbered head ("1. తీపి …"), colon-label
        # head ("అస్థిరమైన సంపద:"), ellipsis line ("…"), attribution ("- దార్ల …"),
        # bare date, or a parenthetical note → end the current padyam, skip line
        if (_HEADING_RE.match(ln) or _SIGN_RE.match(ln) or _DATE_RE.match(ln)
                or _ELLIPSIS_RE.match(ln)
                or (ln.endswith(":") and len(ln) <= 45)
                or ln[:1] in "([（"):
            flush()
            pending_meter = None
            continue
        if len(ln) > LONG_LINE:
            # prose paragraph (intro / note) — end any padyam, record & skip
            flush()
            dropped.append(ln)
            pending_meter = None
            continue
        # a padam line
        if cur is None:
            cur = Padyam(meter=pending_meter)
            pending_meter = None
        cur.lines.append(ln)
    flush()
    return padyalu, dropped


def split_fused(p: Padyam) -> list[Padyam]:
    """Delimiter-less runs of 4-line padyalu (the author omitted the blank
    separator) arrive as one block of 8/12/16 lines. Split an UNMARKED block
    whose length is a multiple of 4 into 4-line padyalu, flagged for review.
    Marked blocks (a declared సీసము etc.) and bhavam-bearing blocks are left
    intact."""
    n = len(p.lines)
    if p.meter or p.bhavam or n < 8 or n % 4 != 0:
        return [p]
    out = []
    for i in range(0, n, 4):
        q = Padyam(meter=None)
        q.lines = p.lines[i:i + 4]
        q.flag = "auto-split-4"
        out.append(q)
    return out


_EMOJI_RE = re.compile(r"[\U0001F000-\U0001FAFF☀-➿←-⇿]")


def is_prose(p: Padyam) -> bool:
    """Reject prose that slipped past the line-level filters: emoji-bearing
    notes, alaṅkāra-śāstra glosses ('ఉదాహరణ:'), or a short block whose lines are
    full sentences (≥6 words ending in a daṇḍa/period)."""
    text = " ".join(p.lines)
    if _EMOJI_RE.search(text) or "ఉదాహరణ" in text or "రచించిన" in text:
        return True
    if len(p.lines) <= 3:
        for L in p.lines:
            if L.rstrip().endswith((".", "।", "...")) and len(L.split()) >= 6:
                return True
    return False


def confident(p: Padyam) -> bool:
    """Precision filter: accept a padyam only if it looks like a real verse."""
    n = len(p.lines)
    if n < 2:                      # single-line fragments are parse noise
        return False
    if n > 12:
        return False
    if max(len(x) for x in p.lines) > LONG_LINE:
        return False
    if is_prose(p):
        return False
    return True


# ---------------------------------------------------------------------------

def load_posts() -> list[dict]:
    manifest = json.loads((RAW / "manifest.json").read_text())
    order = {p["postId"]: i for i, p in enumerate(manifest, 1)}
    out = []
    for fp in POSTS.glob("*.json"):
        d = json.loads(fp.read_text())
        d["idx"] = order.get(d["postId"], 999)
        out.append(d)
    out.sort(key=lambda d: d["idx"])
    return out


if __name__ == "__main__":
    import sys
    want = [int(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else None
    posts = load_posts()
    for d in posts:
        if want and d["idx"] not in want:
            continue
        padyalu, dropped = parse_post(d["body_html"], d["title"])
        good = [p for p in padyalu if confident(p)]
        bad = [p for p in padyalu if not confident(p)]
        if want:
            print("=" * 78)
            print(f"#{d['idx']} {d['title'][:55]}  -> {len(good)} padyalu "
                  f"({len(bad)} rejected, {len(dropped)} prose dropped)")
            for i, p in enumerate(good[:6], 1):
                print(f"  [{i}] meter={p.meter or '-'}  bhavam={'Y' if p.bhavam else '-'}")
                for L in p.lines:
                    print(f"       {L}")
            for p in bad[:4]:
                print(f"  REJECT n={len(p.lines)} meter={p.meter}: {' / '.join(p.lines)[:110]}")
            for pr in dropped[:3]:
                print(f"  PROSE: {pr[:100]}")
