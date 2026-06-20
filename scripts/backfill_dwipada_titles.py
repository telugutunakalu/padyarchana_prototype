"""
Backfill dwipada poem titles to include chapter (and synthetic chapter for the
4 works whose source has no chapter field but does embed a chapter in the file
path, e.g. 'palanati_veera_charitra/003_…txt' → 'ch003').

Approach:
  1. Re-stream dwipada_padartham_results.test5.jsonl, bucket by work,
     and reproduce the EXACT sort order used by the original converter
     (sorted by kanda||"", chapter||"", couplet_number).
  2. For each work, look up MIN(poems.id) by source — that's first_id.
  3. The Nth record in the sorted list maps to poems.id = first_id + N.
  4. Compute the new title and issue an UPDATE for each row.

Title format (matches the new logic in scripts/import_json.py):
  {source} [- {kanda}] [- ch{chapter}] - c{couplet}        when kanda or chapter
  {source} - {couplet}                                      otherwise (won't happen here)
"""
import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
JSONL = ROOT / "dwipada_padartham_results.test5.jsonl"
DB = ROOT / "padyarchana.db"

# Same canonical Telugu titles used by convert_dwipada_jsonl.py.
WORK_TITLE_TELUGU = {
    "ranganatha_ramayanam":          "రంగనాథ రామాయణం",
    "sriramayanam_katta_varadaraju": "శ్రీరామాయణం (కట్టా వరదరాజు)",
    "paramayogi_vilasamu":           "పరమయోగి విలాసము",
    "srinivasa_vilasa_sevadhi":      "శ్రీనివాస విలాస సేవధి",
    "vasishtha_ramayanamu":          "వాశిష్ఠ రామాయణము",
    "saugandhika_prasavapaharanamu": "సౌగంధికా ప్రసవాపహరణము",
    "basava_puranam":                "బసవ పురాణం",
    "dwipada_bhagavatam":            "ద్విపద భాగవతం",
    "sarangadhara_charitramu":       "శారంగధర చరిత్రము",
    "palanati_veera_charitra":       "పల్నాటి వీర చరిత్ర",
    "annamacharya_charitramu":       "అన్నమాచార్య చరిత్రము",
    "srirama_parinayamu":            "శ్రీరామ పరిణయము",
}

# Works whose JSONL has no 'అధ్యాయము' (chapter) — derive a synthetic chapter
# (and sometimes kanda) from the file path.
CHAPTERLESS = {
    "basava_puranam", "dwipada_bhagavatam",
    "palanati_veera_charitra", "sriramayanam_katta_varadaraju",
}

# Flat single-prefix:  palanati_veera_charitra/001_name.txt → ch="001"
FLAT_CH_RE = re.compile(r"/(\d{3,4})_")
# Nested aśvāsam:      basava_puranam/001_outer/003_inner.txt → kanda="outer", ch="001.003"
NESTED_RE = re.compile(r"^[^/]+/(\d{3,4})_([^/]+)/(\d{3,4})_")
# Bhagavatam files:    dwipada_bhagavatam/1_kanda_name.txt → kanda="kanda_name"
BHAG_RE = re.compile(r"^dwipada_bhagavatam/\d+_(.+)\.txt$")


def derive_kanda_chapter(work, raw_kanda, raw_chapter, file_path):
    """Return (kanda, chapter) for backfill, deriving missing pieces from the file path."""
    if raw_kanda or raw_chapter:
        return raw_kanda, raw_chapter
    if work == "basava_puranam":
        m = NESTED_RE.match(file_path or "")
        if m:
            outer_num, outer_name, inner_num = m.group(1), m.group(2), m.group(3)
            return outer_name, f"{outer_num}.{inner_num}"
    if work == "dwipada_bhagavatam":
        m = BHAG_RE.match(file_path or "")
        if m:
            return m.group(1), None
    if work in ("palanati_veera_charitra", "sriramayanam_katta_varadaraju"):
        m = FLAT_CH_RE.search(file_path or "")
        if m:
            return None, m.group(1)
    return None, None


def build_title(source: str, kanda: str | None, chapter: str | None, couplet: int) -> str:
    parts = [source]
    if kanda:
        parts.append(kanda)
    if chapter:
        parts.append(f"ch{chapter}")
    parts.append(f"c{couplet}" if (kanda or chapter) else str(couplet))
    return " - ".join(parts)


def main():
    # 1. Re-stream JSONL, bucket by work.
    buckets: dict[str, list[dict]] = defaultdict(list)
    for line in open(JSONL, encoding="utf-8"):
        d = json.loads(line)
        src = d.get("source", {})
        work = src.get("work")
        if work not in WORK_TITLE_TELUGU:
            continue
        raw_kanda = src.get("కాండము")
        raw_chapter = src.get("అధ్యాయము")
        kanda, chapter = derive_kanda_chapter(work, raw_kanda, raw_chapter, src.get("file"))
        buckets[work].append({
            "kanda":   kanda,
            "chapter": chapter,
            "couplet": src.get("couplet_number"),
        })

    # 2. Sort exactly as the original converter did:
    #    poems.sort(key=lambda p: (p["kanda"] or "", p["chapter"] or "", p["id"] or 0))
    # NOTE: synthetic chapter values must sort identically to the converter's
    # original empty string for chapter-less works. Python's sort is stable so
    # we sort with the SAME key the converter used at import time.
    # At import time, chapter was None for the 4 chapter-less works, so the
    # sort collapsed to ("", "", couplet) — preserve that here for matching.
    for work, recs in buckets.items():
        recs.sort(key=lambda r: (
            r["kanda"] or "",
            (r["chapter"] or "") if work not in CHAPTERLESS else "",  # match original sort
            r["couplet"] or 0,
        ))

    # 3. UPDATE titles by id offset per work.
    con = sqlite3.connect(DB)
    cur = con.cursor()
    updates_total = 0

    for work, recs in buckets.items():
        source_title = WORK_TITLE_TELUGU[work]
        row = cur.execute(
            "SELECT MIN(id), MAX(id), COUNT(*) FROM poems WHERE source = ?",
            (source_title,),
        ).fetchone()
        first_id, last_id, db_count = row
        if first_id is None:
            print(f"[skip] {work}: no rows found for source '{source_title}'")
            continue
        if db_count != len(recs):
            print(f"[abort] {work}: DB count {db_count} != JSONL count {len(recs)}")
            return
        # Contiguity sanity check
        if last_id - first_id + 1 != db_count:
            print(f"[abort] {work}: rows not contiguous (min={first_id} max={last_id} count={db_count})")
            return

        updates = [
            (
                build_title(source_title, r["kanda"], r["chapter"], r["couplet"]),
                first_id + i,
            )
            for i, r in enumerate(recs)
        ]
        cur.executemany("UPDATE poems SET title = ? WHERE id = ?", updates)
        updates_total += cur.rowcount
        print(f"  {work:35s}  updated {len(updates):>6} titles (ids {first_id}..{last_id})")

    con.commit()
    con.close()
    print(f"\nTotal titles updated: {updates_total:,}")


if __name__ == "__main__":
    main()
