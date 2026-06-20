"""
Backfill prathipadartham + bhavam for the 21,400 andhra_mahabharatam padyams
already in padyarchana.db.

Source: andhra_mahabharatam_padartham_results.jsonl (one record per padyam).
Each record's `key` field is `<NNNNNN>__andhra_mahabharatam__c<padyam_number>`,
where NNNNNN is the 0-based position in padyalu_json_data/andhra_mahabharatam.json
(verified — first record matches file_poems[14200] = JSON id 14201). Since our
import preserved order, DB id = first_amb_id + NNNNNN.

For each row we also rebuild `poems.search_text` so the FTS5 trigram index
picks up the new meanings — without this, search would still hit only title +
text + (whatever search_text was at insert time, which was sans padartham).
"""
import json
import sqlite3
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB   = ROOT / "padyarchana.db"
SRC  = ROOT / "andhra_mahabharatam_padartham_results.jsonl"
WORK_TITLE = "శ్రీమదాంధ్ర మహాభారతము"


def build_search_text(title, text, bhavam, prathi):
    parts = []
    if title:  parts.append(title)
    if text:   parts.append(text)
    if bhavam: parts.append(bhavam)
    for e in (prathi or []):
        w, m = e.get("word"), e.get("meaning")
        if w: parts.append(w)
        if m: parts.append(m)
    return "\n".join(p for p in parts if p)


def main():
    con = sqlite3.connect(DB)
    con.execute("PRAGMA cache_size = -128000")
    cur = con.cursor()

    first_id = cur.execute(
        "SELECT MIN(id) FROM poems WHERE source = ?", (WORK_TITLE,)
    ).fetchone()[0]
    if first_id is None:
        raise SystemExit(f"No poems found for source {WORK_TITLE!r}")

    print(f"First DB id for source: {first_id}")
    print("Loading existing title+text for all andhra_mahabharatam rows …")
    row_index = {
        r[0]: (r[1], r[2])
        for r in cur.execute(
            "SELECT id, title, text FROM poems WHERE source = ?", (WORK_TITLE,)
        )
    }
    print(f"  rows loaded: {len(row_index):,}")

    print("Streaming JSONL …")
    updates = []
    not_found = 0
    dropped_padartham = 0
    t0 = time.perf_counter()
    for line in open(SRC, encoding="utf-8"):
        j = json.loads(line)
        pos = int(j["key"].split("__")[0])
        db_id = first_id + pos
        if db_id not in row_index:
            not_found += 1
            continue
        title, text = row_index[db_id]

        raw_prathi = j["result"].get("prathipadartham") or []
        prathi = []
        for e in raw_prathi:
            p, a = e.get("padam"), e.get("artham")
            if p and a:
                prathi.append({"word": p, "meaning": a})
            else:
                dropped_padartham += 1
        bhavam = (j["result"].get("bhavam") or "").strip() or None

        st = build_search_text(title, text, bhavam, prathi)
        updates.append((
            json.dumps(prathi, ensure_ascii=False) if prathi else None,
            bhavam,
            st,
            db_id,
        ))

    print(f"  prepared {len(updates):,} updates (not_found={not_found}, "
          f"dropped_padartham={dropped_padartham}) in {time.perf_counter() - t0:.1f}s")

    # UPDATE in batches — FTS5 triggers fire on each row.
    batch_size = 1000
    print(f"Applying UPDATEs in batches of {batch_size} …")
    t0 = time.perf_counter()
    for i in range(0, len(updates), batch_size):
        batch = updates[i:i + batch_size]
        cur.executemany(
            "UPDATE poems SET prathipadartham = ?, bhavam = ?, search_text = ? "
            "WHERE id = ?",
            batch,
        )
        con.commit()
        print(f"  {min(i + batch_size, len(updates)):>7,} / {len(updates):,}  "
              f"({time.perf_counter() - t0:.1f}s)")

    # Final stats.
    with_p = cur.execute(
        "SELECT COUNT(*) FROM poems WHERE source = ? AND prathipadartham IS NOT NULL",
        (WORK_TITLE,),
    ).fetchone()[0]
    with_b = cur.execute(
        "SELECT COUNT(*) FROM poems WHERE source = ? AND bhavam IS NOT NULL",
        (WORK_TITLE,),
    ).fetchone()[0]
    n_fts = cur.execute("SELECT COUNT(*) FROM poems_fts").fetchone()[0]
    n_poems = cur.execute("SELECT COUNT(*) FROM poems").fetchone()[0]
    print()
    print(f"Coverage after backfill:")
    print(f"  with prathipadartham: {with_p:,} / 21,400")
    print(f"  with bhavam:          {with_b:,} / 21,400")
    print(f"  FTS rows == poems? {n_fts} == {n_poems}? {n_fts == n_poems}")
    con.close()


if __name__ == "__main__":
    main()
