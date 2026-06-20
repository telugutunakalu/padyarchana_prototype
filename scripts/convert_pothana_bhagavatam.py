"""
Convert pothana_bhagavatam.jsonl into the padyalu_json_data/ JSON schema
used by scripts/import_json.py.

Source record shape:
    { "skanda": "5.1", "skanda_title": "...", "ghatta": 12, "ghatta_title": "...",
      "padyam_label": "5.1-12-క.", "meter": "...", "padyam": "...",
      "tika": "word = meaning; word = meaning; ...", "bhavam": "...",
      "source_url": "..." }

Output is one file `padyalu_json_data/pothana_bhagavatam.json` with the standard
padyalu_json_data schema (matches what the importer reads).
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC = ROOT / "pothana_bhagavatam.jsonl"
DST = ROOT / "padyalu_json_data" / "pothana_bhagavatam.json"

WORK_TITLE = "శ్రీమదాంధ్ర మహాభాగవతం"
AUTHOR = "బమ్మెర పోతన"
LITERARY_FORM = "పురాణం"
DEFAULT_METER_WHEN_EMPTY = "వచనము"  # empty meter ≈ prose passage

# Normalize meter names from this source to the canonical names in the DB.
METER_REMAP = {
    "కందం": "కందము",                              # → id 41
    "సీసం + తేటగీతి": "సీసము + తేటగీతి",         # → id 38
    "సీసం + ఆటవెలది": "సీసము + ఆటవెలది",         # new (canonical form)
    "సీసం2 + ఆటవెలది": "సీసము2 + ఆటవెలది",
    "సీసం2 + తేటగీతి": "సీసము2 + తేటగీతి",
}


def normalize_meter(m: str | None) -> str:
    if not m:
        return DEFAULT_METER_WHEN_EMPTY
    return METER_REMAP.get(m, m)


def strip_editorial_prefix(padyam: str) -> str:
    """Some padyams (8 of 9013) start with an editorial header line like
    '- తెలుగుభాగవతం పీఠిక^ భూమిక\\n\\n<verse...>' or '^ భూమిక\\n\\n<verse...>'.
    Strip the header lines."""
    if not padyam.startswith(("-", "^")):
        return padyam
    # Drop everything up to and including the first blank line; if there's no
    # blank line, drop only the leading line that begins with '-' or '^'.
    if "\n\n" in padyam:
        return padyam.split("\n\n", 1)[1]
    head, _, rest = padyam.partition("\n")
    return rest if (head.startswith(("-", "^"))) else padyam


def split_top_level_semicolons(s: str):
    """Split on `;` but skip semicolons inside {...} blocks (27 occurrences)."""
    parts, depth, start = [], 0, 0
    for i, ch in enumerate(s):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth = max(0, depth - 1)
        elif ch == ";" and depth == 0:
            parts.append(s[start:i])
            start = i + 1
    parts.append(s[start:])
    return parts


def parse_tika(tika: str):
    """Parse 'word = meaning; word = meaning; ...' into prathipadartham."""
    entries = []
    dropped = 0
    if not tika:
        return entries, dropped
    for part in split_top_level_semicolons(tika):
        p = part.strip()
        if not p:
            continue
        if "=" not in p:
            dropped += 1
            continue
        word, _, meaning = p.partition("=")
        word, meaning = word.strip(), meaning.strip().rstrip(".")
        if word and meaning:
            entries.append({"word": word, "meaning": meaning})
        else:
            dropped += 1
    return entries, dropped


def skanda_sort_key(s: str):
    """Sort skanda numerically with sub-skanda handling: '5.1' > '5' but '5.1' < '6'."""
    try:
        major, _, minor = s.partition(".")
        return (int(major), int(minor) if minor else 0)
    except Exception:
        return (999, 0)


def main():
    records = []
    skipped_empty = 0
    meter_counts = Counter()
    tika_dropped_total = 0

    with open(SRC, encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            raw_padyam = d.get("padyam") or ""
            verse = strip_editorial_prefix(raw_padyam).strip()
            if not verse:
                skipped_empty += 1
                continue
            lines = [ln for ln in verse.split("\n") if ln.strip()]
            if not lines:
                skipped_empty += 1
                continue

            meter = normalize_meter(d.get("meter"))
            meter_counts[meter] += 1

            prathi, dropped = parse_tika(d.get("tika") or "")
            tika_dropped_total += dropped

            records.append({
                "skanda":        d.get("skanda"),
                "skanda_title":  d.get("skanda_title"),
                "ghatta":        d.get("ghatta"),
                "ghatta_title":  d.get("ghatta_title"),
                "padyam_label":  d.get("padyam_label"),
                "meter":         meter,
                "lines":         lines,
                "prathipadartham": prathi,
                "bhavam":        d.get("bhavam") or None,
                "source_url":    d.get("source_url"),
            })

    # Sort by (skanda, ghatta, source order — stable)
    records.sort(key=lambda r: (skanda_sort_key(r["skanda"] or ""), r["ghatta"] or 0))

    # Re-number couplet_in_chapter per (skanda, ghatta) so the importer's
    # title becomes  '<work> - <skanda_title> - ch<ghatta> - c<n>'
    counters = defaultdict(int)
    poems_out = []
    for r in records:
        key = (r["skanda"], r["ghatta"])
        counters[key] += 1
        poems_out.append({
            "id":            counters[key],          # couplet number WITHIN this chapter
            "lines_telugu":  r["lines"],
            "Chandassu":     r["meter"],
            "kanda":         r["skanda_title"],
            "chapter":       str(r["ghatta"]) if r["ghatta"] is not None else None,
            "chapter_title": r["ghatta_title"],
            "padyam_label":  r["padyam_label"],      # preserved for reference
            "prathipadartham": r["prathipadartham"],
            "bhavam":        r["bhavam"],
            "source_url":    r["source_url"],
        })

    out = {
        "shatakam_title_telugu": WORK_TITLE,
        "author_telugu":         AUTHOR,
        "year":                  None,
        "literary_form_telugu":  LITERARY_FORM,
        "meter_telugu":          DEFAULT_METER_WHEN_EMPTY,
        "poems":                 poems_out,
    }

    DST.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {len(poems_out):,} poems → {DST}")
    print(f"Skipped empty padyams: {skipped_empty}")
    print(f"Tika entries dropped (malformed segments): {tika_dropped_total}")
    print(f"\nMeter distribution (top 15):")
    for m, c in meter_counts.most_common(15):
        print(f"  {m:40s}  {c}")
    print(f"  (… {len(meter_counts) - 15} more meter values)" if len(meter_counts) > 15 else "")


if __name__ == "__main__":
    main()
