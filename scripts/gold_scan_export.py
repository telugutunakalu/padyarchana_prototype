"""
Gold auto-tagging — step 1 of 3: export scan candidates.

Writes poems that have a genuine metrical category (skips unknown/prose, which
can never match a single chandassu) into chunked JSON files the browser-based
scanner reads. Run:  ./venv/bin/python scripts/gold_scan_export.py
"""
import sqlite3, json, os, shutil

DB = "padyarchana.db"
OUT_DIR = "static/_goldscan"
CHUNK = 30000
# Recorded "meters" that are not a single chandassu and can never match.
SKIP = ("unknown", "Unknown", "UNKNOWN", "వచనము", "గద్యము", "గద్య", "గద్యం")


def main():
    if os.path.isdir(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR)

    con = sqlite3.connect(DB)
    placeholders = ",".join("?" * len(SKIP))
    rows = con.execute(
        f"""SELECT p.id, p.text, m.name
            FROM poems p JOIN meters m ON p.meter_id = m.id
            WHERE p.text IS NOT NULL AND p.text != ''
              AND m.name NOT IN ({placeholders})
            ORDER BY p.id""",
        SKIP,
    ).fetchall()
    con.close()

    chunks = 0
    for i in range(0, len(rows), CHUNK):
        part = [{"id": r[0], "text": r[1], "meter": r[2]} for r in rows[i:i + CHUNK]]
        with open(f"{OUT_DIR}/chunk_{chunks:03d}.json", "w", encoding="utf-8") as f:
            json.dump(part, f, ensure_ascii=False)
        chunks += 1

    with open(f"{OUT_DIR}/meta.json", "w", encoding="utf-8") as f:
        json.dump({"candidates": len(rows), "chunks": chunks, "chunk_size": CHUNK}, f)

    print(f"exported {len(rows)} candidates into {chunks} chunks of {CHUNK}")


if __name__ == "__main__":
    main()
