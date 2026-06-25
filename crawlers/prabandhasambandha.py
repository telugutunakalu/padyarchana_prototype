#!/usr/bin/env python3
"""Structure ప్రబంధసంబంధబంధనిబంధనగ్రంథము (మండపాక పార్వతీశ్వర శాస్త్రి, 1896).

A proofread single-page treatise on బంధకవిత్వము (figure/constrained poetry): bandha
example verses interleaved with prose explanations. Reuses the general clean-text
parser, whose long-line logic flushes/skips the prose paragraphs automatically.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import wikisource_crawler as w
import text_to_json as t

OUT = Path(__file__).resolve().parent.parent / "padyalu_json_data"
WORK = "ప్రబంధసంబంధబంధనిబంధనగ్రంథము"


def main():
    poems = t.parse_padyalu(w.fetch_rendered(WORK))
    poems = [{"id": i, **p} for i, p in enumerate(poems, 1)]
    rec = {
        "shatakam_title_telugu": WORK,
        "author_telugu": "మండపాక పార్వతీశ్వర శాస్త్రి",
        "year": 1896,
        "literary_form_telugu": "బంధకవిత్వము",
        "source_url": "https://te.wikisource.org/wiki/" + WORK,
        "poems": poems,
    }
    OUT.mkdir(exist_ok=True)
    fp = OUT / "prabandhasambandhabandhanibandhanagranthamu_mandapaka_parvatisvara_sastri.json"
    fp.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"-> {fp.name} ({len(poems)} padyalu)")


if __name__ == "__main__":
    main()
