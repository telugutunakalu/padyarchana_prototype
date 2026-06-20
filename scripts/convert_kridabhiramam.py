"""
Convert kridabhiramam_padartham_results.jsonl → padyalu_json_data/kridabhiramam.json
(the same schema scripts/import_json.py reads).

Source: 296 padyams from క్రీడాభిరామం by వినుకొండ వల్లభరాయుడు, a 14th–15th c.
Vīdhi-nāṭakam (campū). Each record carries:
    source.{work, padyam_number, గ్రంథము, సాహిత్యరూపము, రచయిత, శీర్షిక, ఛందస్సు, కాలము}
    poem            – verse text, lines joined by '\\n'
    result.prathipadartham – list of {padam, artham}
    result.bhavam   – prose meaning

Output mirrors what the dwipada / Mahabharatam / Pothana onboardings produced
so import_json.py can ingest with --skip-duplicate-check unchanged.

Notes:
  • No kanda concept in this work; sections (శీర్షిక) are topical headings
    rather than chapters. They go into `chapter` so the importer's title
    becomes 'క్రీడాభిరామం - <section> - c<n>'.
  • 8 records have padyam_number=None. We renumber sequentially by JSONL
    stream order (1..296) for the importer's c{N}; the original padyam_number
    (or None) is preserved as `padyam_number` per-record metadata.
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC = ROOT / "kridabhiramam_padartham_results.jsonl"
DST = ROOT / "padyalu_json_data" / "kridabhiramam.json"

WORK_TITLE     = "క్రీడాభిరామం"
AUTHOR         = "వినుకొండ వల్లభరాయుడు"
LITERARY_FORM  = "వీధి నాటకము (చంపూ)"
ERA            = "14వ శతాబ్దం చివర – 15వ శతాబ్దం ప్రారంభం"
DEFAULT_METER  = "వచనము"


def main():
    records_in = []
    for line in open(SRC, encoding="utf-8"):
        records_in.append(json.loads(line))

    poems_out = []
    meters = Counter()
    sections = Counter()
    tika_dropped = 0
    empty_poems = 0

    for idx, d in enumerate(records_in, start=1):
        src = d.get("source", {})
        res = d.get("result", {})

        raw_poem = (d.get("poem") or "").strip()
        if not raw_poem:
            empty_poems += 1
            continue
        lines = [ln for ln in raw_poem.split("\n") if ln.strip()]

        # Per-poem meter, falling back to వచనము if absent (all 296 have it
        # in this corpus, but be defensive).
        meter = (src.get("ఛందస్సు") or "").strip() or DEFAULT_METER
        meters[meter] += 1

        section = (src.get("శీర్షిక") or "").strip() or None
        if section:
            sections[section] += 1

        # Map padam/artham → word/meaning for the DB schema.
        prathi = []
        for e in (res.get("prathipadartham") or []):
            p, a = e.get("padam"), e.get("artham")
            if p and a:
                prathi.append({"word": p, "meaning": a})
            else:
                tika_dropped += 1

        bhavam = (res.get("bhavam") or "").strip() or None

        poems_out.append({
            "id":               idx,                                  # 1..296, drives c{N} in the title
            "padyam_number":    src.get("padyam_number"),             # preserved as metadata
            "lines_telugu":     lines,
            "Chandassu":        meter,
            "chapter":          section,                              # section heading → 'chapter' slot in the importer
            "chapter_title":    section,
            "prathipadartham":  prathi,
            "bhavam":           bhavam,
        })

    out = {
        "shatakam_title_telugu": WORK_TITLE,
        "author_telugu":         AUTHOR,
        "year":                  None,
        "era_telugu":            ERA,
        "literary_form_telugu":  LITERARY_FORM,
        "meter_telugu":          DEFAULT_METER,
        "poems":                 poems_out,
    }
    DST.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {len(poems_out):,} padyams → {DST}")
    print(f"  empty padyams skipped: {empty_poems}")
    print(f"  prathipadartham entries dropped (malformed): {tika_dropped}")
    print()
    print("Meter distribution:")
    for m, c in meters.most_common():
        print(f"  {m:30s}  {c}")
    print(f"\nDistinct sections (శీర్షిక): {len(sections)}")


if __name__ == "__main__":
    main()
