"""
Generate a Gemini batch-request JSONL for prathipadartham + bhavam, for every
NON-dwipada poem in the server DB (padyarchana.db).

- Source of truth: padyarchana.db (poems / poets / meters).
- Excludes dwipada poems (meter "ద్విపద", id 47). Pothana Bhagavatam is not in
  the DB, so nothing extra to drop there.
- Key format follows the existing convention:  {globalIdx:06d}__{slug}__c{N}
  where slug is the english work name (from the JSON filenames) and N is the
  1-indexed poem number within that work.

Usage:
    python scripts/generate_padartham_requests.py [output.jsonl]
"""
import glob
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB = ROOT / "padyarchana.db"
JSON_DIR = ROOT / "padyalu_json_data"
DWIPADA_METER_ID = 47

SYSTEM_TEXT = (
    "Telugu & Sanskrit scholar. For the Telugu పద్యం below, give its "
    "prathipadartham (word-by-word meaning — every padam in order, with its "
    "artham) and bhavam (overall meaning), in Telugu only."
)

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "prathipadartham": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "padam": {"type": "STRING"},
                    "artham": {"type": "STRING"},
                },
                "required": ["padam", "artham"],
                "propertyOrdering": ["padam", "artham"],
            },
        },
        "bhavam": {"type": "STRING"},
    },
    "required": ["prathipadartham", "bhavam"],
    "propertyOrdering": ["prathipadartham", "bhavam"],
}


def build_title_to_slug():
    """Map shatakam_title_telugu -> english slug (JSON filename stem)."""
    title2slug = {}
    for fp in glob.glob(str(JSON_DIR / "*.json")):
        stem = os.path.splitext(os.path.basename(fp))[0]
        try:
            with open(fp, encoding="utf-8") as f:
                d = json.load(f)
            title = d.get("shatakam_title_telugu")
        except Exception:
            # Some files have invalid JSON escapes; recover just the title.
            head = open(fp, encoding="utf-8").read(4000)
            m = re.search(r'"shatakam_title_telugu"\s*:\s*"([^"]+)"', head)
            title = m.group(1) if m else None
        if title:
            title2slug.setdefault(title, stem)
    return title2slug


def slug_for(source, title2slug):
    if source in title2slug:
        return title2slug[source]
    # Already-english source value (e.g. 'manchimaata_satakam').
    if source and source.isascii():
        return source
    return None


def main():
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "non_dwipada_padartham_requests.jsonl"

    title2slug = build_title_to_slug()

    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    # All non-dwipada poems with author name. Order: by work (min poem id),
    # then poem id — keeps each work contiguous and in import order.
    rows = cur.execute(
        """
        SELECT p.id, p.text, p.source, COALESCE(po.name, 'Unknown') AS author
        FROM poems p
        LEFT JOIN poets po ON p.poet_id = po.id
        WHERE p.meter_id IS NULL OR p.meter_id != ?
        ORDER BY p.source, p.id
        """,
        (DWIPADA_METER_ID,),
    ).fetchall()

    # Determine a stable work ordering by each work's minimum poem id.
    work_min_id = {}
    for pid, _text, source, _author in rows:
        if source not in work_min_id or pid < work_min_id[source]:
            work_min_id[source] = pid

    # Group poems per source, preserving poem.id order.
    by_source = {}
    for pid, text, source, author in rows:
        by_source.setdefault(source, []).append((pid, text, author))

    ordered_sources = sorted(by_source, key=lambda s: work_min_id[s])

    unmapped = set()
    global_idx = 0
    written = 0
    with open(out_path, "w", encoding="utf-8") as out:
        for source in ordered_sources:
            slug = slug_for(source, title2slug)
            if slug is None:
                unmapped.add(source)
                slug = "unknown_source"
            for n, (pid, text, author) in enumerate(by_source[source], start=1):
                content = f"{text}\nSource: {source}, author: {author}"
                record = {
                    "key": f"{global_idx:06d}__{slug}__c{n}",
                    "request": {
                        "model": "models/gemini-3.1-flash-lite",
                        "systemInstruction": {"parts": [{"text": SYSTEM_TEXT}]},
                        "contents": [{"role": "user", "parts": [{"text": content}]}],
                        "generationConfig": {
                            "responseMimeType": "application/json",
                            "responseSchema": RESPONSE_SCHEMA,
                        },
                    },
                }
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                global_idx += 1
                written += 1

    conn.close()
    print(f"Wrote {written} records to {out_path}")
    print(f"Works (sources): {len(ordered_sources)}")
    if unmapped:
        print(f"WARNING: {len(unmapped)} source(s) had no slug mapping: {sorted(unmapped)}")
    else:
        print("All sources mapped to a slug.")


if __name__ == "__main__":
    main()
