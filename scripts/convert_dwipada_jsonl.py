"""
Stream dwipada_padartham_results.test5.jsonl into 12 per-work JSON files
under padyalu_json_data/.

Source line shape:
    { "key": "...", "source": {...}, "poem": "line1\nline2", "result": {...} }

Output file shape (matches the existing padyalu_json_data/*.json schema, plus
the new prathipadartham/bhavam/kanda fields):
    {
      "shatakam_title_telugu": "...",
      "author_telugu": "...",
      "year": null,
      "literary_form_telugu": "ద్విపదకావ్యం",
      "meter_telugu": "ద్విపద",
      "poems": [
        {
          "id": <couplet_number>,
          "lines_telugu": [...],
          "Chandassu": "ద్విపద",
          "kanda": "...",
          "chapter": "...",
          "chapter_title": "...",
          "prathipadartham": [ {"word": ..., "meaning": ...}, ... ],
          "bhavam": "..."
        },
        ...
      ]
    }
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

SRC = Path(__file__).parent.parent / "dwipada_padartham_results.test5.jsonl"
OUT_DIR = Path(__file__).parent.parent / "padyalu_json_data"

# work key -> canonical Telugu title (edit before re-running if any are wrong)
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


def transform_padartham(items):
    """JSONL uses padam/artham — DB schema uses word/meaning."""
    out = []
    for it in items or []:
        word = it.get("padam") or it.get("word")
        meaning = it.get("artham") or it.get("meaning")
        if word and meaning:
            out.append({"word": word, "meaning": meaning})
    return out


def main():
    if not SRC.exists():
        print(f"ERROR: source file not found: {SRC}", file=sys.stderr)
        sys.exit(1)

    buckets = defaultdict(list)        # work -> list[poem dict]
    authors = {}                       # work -> author string
    unknown_works = set()

    with open(SRC, encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            src = d.get("source", {})
            res = d.get("result", {})
            work = src.get("work")
            if not work:
                continue
            if work not in WORK_TITLE_TELUGU:
                unknown_works.add(work)
                continue

            authors.setdefault(work, src.get("రచయిత") or "Unknown")

            poem_text = d.get("poem", "")
            lines = [ln for ln in poem_text.split("\n") if ln.strip()]

            buckets[work].append({
                "id": src.get("couplet_number"),
                "lines_telugu": lines,
                "Chandassu": "ద్విపద",
                "kanda": src.get("కాండము"),
                "chapter": src.get("అధ్యాయము"),
                "chapter_title": src.get("శీర్షిక"),
                "prathipadartham": transform_padartham(res.get("prathipadartham")),
                "bhavam": res.get("bhavam") or None,
            })

    if unknown_works:
        print(f"WARN: skipped records from unmapped works: {sorted(unknown_works)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for work, poems in buckets.items():
        # Sort by (kanda, chapter, couplet_number) for deterministic order
        poems.sort(key=lambda p: (p["kanda"] or "", p["chapter"] or "", p["id"] or 0))
        out = {
            "shatakam_title_telugu": WORK_TITLE_TELUGU[work],
            "author_telugu": authors[work],
            "year": None,
            "literary_form_telugu": "ద్విపదకావ్యం",
            "meter_telugu": "ద్విపద",
            "poems": poems,
        }
        out_path = OUT_DIR / f"{work}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"  wrote {len(poems):>6} poems → {out_path.name}")

    print(f"\nTotal works written: {len(buckets)}")
    print(f"Total couplets: {sum(len(v) for v in buckets.values()):,}")


if __name__ == "__main__":
    main()
