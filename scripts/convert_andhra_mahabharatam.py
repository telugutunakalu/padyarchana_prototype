"""
Parse andhramahabharatam.txt → padyalu_json_data/andhra_mahabharatam.json
(the same schema scripts/import_json.py reads).

Source format (~22.7k verses, ~53k lines):

  # <html-page-marker>.txt           ← editorial page break, IGNORED
  <Parva> - <Ashwasa>                ← e.g. "ఆదిపర్వము - ప్రథమాశ్వాసము"
  <SectionHeading>                   ← e.g. "మంగళశ్లోకము", "భారతకథాప్రస్తావన"
  <meter-abbr>. <verse line 1>       ← e.g. "శా. శ్రీవాణీగిరిజా..."
  <verse line 2>
  ...
  <verse last line>. <verse_number>  ← number is on its own at end of last line

The sīsa form is two stanzas in print (4 lines of 'సీ.' + 2 lines of 'ఆ.' or 'తే.'),
but it is conventionally ONE padyam. Only the trailing 'ఆ.'/'తే.' carries the
verse number; we merge the two into a single padyam with combined Chandassu.
"""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC = ROOT / "andhramahabharatam.txt"
DST = ROOT / "padyalu_json_data" / "andhra_mahabharatam.json"

WORK_TITLE = "శ్రీమదాంధ్ర మహాభారతము"
AUTHOR     = "నన్నయ, తిక్కన, ఎర్రాప్రెగడ"
LITERARY_FORM = "మహాకావ్యం"

# Meter abbreviation → canonical name (matching the DB's consolidated meter rows).
METER_ABBR = {
    "వ":     "వచనము",
    "క":     "కందము",
    "తే":    "తేటగీతి",
    "ఆ":     "ఆటవెలది",
    "సీ":    "సీసము",
    "చ":     "చంపకమాల",
    "ఉ":     "ఉత్పలమాల",
    "మ":     "మత్తేభవిక్రీడితము",
    "శా":    "శార్దూలవిక్రీడితము",
    "గద్య":  "గద్యము",
    "దండక":  "తగణ దండకము",
}

# Full-name meters that appear at line start.
FULL_NAME_METERS = {
    "మాలిని", "మత్తకోకిల", "తరలము", "మహాస్రగ్ధర", "స్రగ్ధర", "లయగ్రాహి",
    "ఉత్సాహము", "మానిని", "తోటకము", "వనమయూరము", "లయవిభాతి",
    "భుజంగప్రయాతము", "స్రగ్విణీ", "కవిరాజవిరాజితము", "మంగళమహశ్రీ",
    "ఇంద్రవజ్రము", "ఉపేంద్రవజ్రము", "పంచచామరము",
}

ABBR_RE       = re.compile(r"^([ఀ-౿]{1,5})\.\s")          # 'శా. ' / 'క. ' / 'గద్య. '
FULLNAME_RE   = re.compile(r"^(" + "|".join(re.escape(m) for m in FULL_NAME_METERS) + r")\s")
# Capture both 'ప్రథమాశ్వాసము' (ms preceded by ా matra) and a literal 'ఆశ్వాసము'.
PARVA_ASH_RE  = re.compile(r"^(.+?పర్వము)\s*-\s*(.+?శ్వాసము)\s*$")
PARVA_END_RE  = re.compile(r"పర్వము\s*సమాప్తము")
PAGE_MARK_RE  = re.compile(r"^#\s+\S+\.txt$")
TRAILING_NUM  = re.compile(r"[\s\.\!\?\"\'‘’“”]+(\d+)\s*$")


def meter_from_line(line: str) -> str | None:
    m = ABBR_RE.match(line)
    if m:
        abbr = m.group(1)
        if abbr in METER_ABBR:
            return METER_ABBR[abbr]
        return None
    m = FULLNAME_RE.match(line)
    if m:
        return m.group(1)
    return None


def is_verse_start(line: str) -> bool:
    return meter_from_line(line) is not None


def strip_meter_prefix(line: str) -> str:
    """Drop the leading 'X. ' / full-name from a verse-start line."""
    m = ABBR_RE.match(line)
    if m:
        return line[m.end():]
    m = FULLNAME_RE.match(line)
    if m:
        return line[m.end():]
    return line


def extract_trailing_number(line: str):
    m = TRAILING_NUM.search(line)
    if not m:
        return None, line
    n = int(m.group(1))
    body = line[:m.start()] + line[m.start():m.start() + (m.end() - m.start() - len(m.group(1)))].rstrip()
    return n, body.rstrip()


def main():
    poems_out = []
    seq_id = 0

    parva = None
    ashwasa = None
    section = None

    # Verse accumulator.
    cur_lines: list[str] = []
    cur_meter: str | None = None
    cur_combined_meter: str | None = None  # used for sīsa + ఆట/తే

    stats = Counter()
    anomalies = []

    def emit():
        nonlocal seq_id
        if not cur_lines:
            return
        # Try to pull trailing verse-number off the last line.
        last = cur_lines[-1]
        num, body = extract_trailing_number(last)
        if body != last:
            cur_lines[-1] = body
        meter = cur_combined_meter or cur_meter or "Unknown"
        seq_id += 1
        poems_out.append({
            "id":             seq_id,
            "padyam_number":  num,
            "lines_telugu":   [ln for ln in cur_lines if ln.strip()],
            "Chandassu":      meter,
            "kanda":          parva,
            "chapter":        ashwasa,
            "chapter_title":  section,
        })
        stats[meter] += 1
        if num is None:
            anomalies.append({"id": seq_id, "reason": "no trailing number", "lines": cur_lines[:2]})

    def reset_verse():
        nonlocal cur_lines, cur_meter, cur_combined_meter
        cur_lines = []
        cur_meter = None
        cur_combined_meter = None

    with open(SRC, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip()
            if not line.strip():
                continue
            if PAGE_MARK_RE.match(line):
                continue

            # Parva + Ashwasa header  ("X-Parva - Y-Ashwasa")
            m = PARVA_ASH_RE.match(line)
            if m:
                # emit any verse-in-progress before switching context
                emit()
                reset_verse()
                parva = m.group(1).strip()
                ashwasa = m.group(2).strip()
                section = None
                continue

            # End-of-parva marker ("X-Parva-Name samaptamu")
            if PARVA_END_RE.search(line):
                emit()
                reset_verse()
                continue

            new_meter = meter_from_line(line)
            if new_meter:
                # Special case: sīsa stanza without a number, immediately followed
                # by ఆట/తే stanza — these print as one padyam in the source.
                if cur_meter == "సీసము" and new_meter in ("ఆటవెలది", "తేటగీతి"):
                    cur_lines.append(strip_meter_prefix(line))
                    cur_combined_meter = (
                        "సీసము + ఆటవెలది" if new_meter == "ఆటవెలది" else "సీసము + తేటగీతి"
                    )
                    n, _ = extract_trailing_number(line)
                    if n is not None:
                        emit()
                        reset_verse()
                    continue

                # Otherwise this is a fresh verse start.
                emit()
                reset_verse()
                cur_meter = new_meter
                cur_lines = [strip_meter_prefix(line)]
                n, _ = extract_trailing_number(line)
                if n is not None:
                    emit()
                    reset_verse()
                continue

            # Continuation line of an active verse.
            if cur_lines:
                cur_lines.append(line)
                n, _ = extract_trailing_number(line)
                if n is not None:
                    emit()
                    reset_verse()
                continue

            # Floating line outside a verse → treat as a section heading.
            section = line.strip()

    # Anything left in the buffer at EOF (no more parva marker)?
    emit()

    out = {
        "shatakam_title_telugu": WORK_TITLE,
        "author_telugu":         AUTHOR,
        "year":                  None,
        "literary_form_telugu":  LITERARY_FORM,
        "poems":                 poems_out,
    }
    DST.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {len(poems_out):,} padyams → {DST}")
    print()
    print("Meter distribution (top 20):")
    for m, c in stats.most_common(20):
        print(f"  {m:35s}  {c:>6}")
    print()
    print(f"Padyams missing a trailing number: {len(anomalies)}")
    for a in anomalies[:5]:
        print(f"  id={a['id']}  reason={a['reason']}")
        for ln in a['lines']:
            print(f"     {ln[:90]}")

    # Per-parva summary
    print()
    print("Per-parva counts:")
    pp = Counter(p["kanda"] for p in poems_out)
    for k, c in sorted(pp.items(), key=lambda x: -x[1]):
        print(f"  {k!r:30s}  {c:>5}")


if __name__ == "__main__":
    main()
