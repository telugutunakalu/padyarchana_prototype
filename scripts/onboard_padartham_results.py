"""
Onboard non_dwipada_padartham_results.test5.jsonl into padyarchana.db.

For every result, write:
  - poems.prathipadartham : JSON list of {"word", "meaning"} (remapped from
    the result's {"padam", "artham"}), in original order.
  - poems.bhavam          : the result's bhavam text.

Mapping is by the key's 6-digit global index against the generator's ordering,
and is re-validated against each result's embedded poem text before any write.
A non-matching record is skipped and reported (not written).

Run scripts/analyze_padartham_results.py first. Back up the DB before running.
"""
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB = ROOT / "padyarchana.db"
RESULTS = ROOT / "non_dwipada_padartham_results.test5.jsonl"
DWIPADA_METER_ID = 47


def ordered_poem_ids(cur):
    rows = cur.execute(
        """
        SELECT p.id, p.source
        FROM poems p
        WHERE p.meter_id IS NULL OR p.meter_id != ?
        ORDER BY p.source, p.id
        """,
        (DWIPADA_METER_ID,),
    ).fetchall()
    work_min_id = {}
    for pid, source in rows:
        if source not in work_min_id or pid < work_min_id[source]:
            work_min_id[source] = pid
    by_source = {}
    for pid, source in rows:
        by_source.setdefault(source, []).append(pid)
    ordered = []
    for source in sorted(by_source, key=lambda s: work_min_id[s]):
        ordered.extend(by_source[source])
    return ordered


def norm(t):
    return "\n".join(line.rstrip() for line in (t or "").strip().splitlines())


def main():
    results_path = Path(sys.argv[1]) if len(sys.argv) > 1 else RESULTS

    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    ordered = ordered_poem_ids(cur)
    text_by_id = {pid: txt for pid, txt in cur.execute("SELECT id, text FROM poems")}

    updates = []          # (prathipadartham_json, bhavam, poem_id)
    skipped_text = 0
    skipped_empty = 0

    with open(results_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            idx = int(d["key"][:6])
            if idx >= len(ordered):
                skipped_text += 1
                continue
            pid = ordered[idx]

            # guard: never write to a poem whose text doesn't match the result
            if norm(d.get("poem")) != norm(text_by_id.get(pid)):
                skipped_text += 1
                continue

            res = d.get("result") or {}
            pp = res.get("prathipadartham") or []
            bhavam = (res.get("bhavam") or "").strip() or None
            entries = [
                {"word": e["padam"], "meaning": e["artham"]}
                for e in pp
                if "padam" in e and "artham" in e
            ]
            if not entries and not bhavam:
                skipped_empty += 1
                continue

            pp_json = (
                json.dumps(entries, ensure_ascii=False, separators=(",", ":"))
                if entries else None
            )
            updates.append((pp_json, bhavam, pid))

    cur.executemany(
        "UPDATE poems SET prathipadartham=?, bhavam=?, "
        "updated_at=CURRENT_TIMESTAMP WHERE id=?",
        updates,
    )
    conn.commit()

    # verify
    have_pp = cur.execute(
        "SELECT COUNT(*) FROM poems WHERE (meter_id IS NULL OR meter_id!=?) "
        "AND prathipadartham IS NOT NULL AND prathipadartham!=''",
        (DWIPADA_METER_ID,),
    ).fetchone()[0]
    have_bh = cur.execute(
        "SELECT COUNT(*) FROM poems WHERE (meter_id IS NULL OR meter_id!=?) "
        "AND bhavam IS NOT NULL AND bhavam!=''",
        (DWIPADA_METER_ID,),
    ).fetchone()[0]
    conn.close()

    print(f"updated rows:                 {len(updates)}")
    print(f"skipped (text mismatch/range): {skipped_text}")
    print(f"skipped (empty result):        {skipped_empty}")
    print(f"non-dwipada poems with prathipadartham now: {have_pp}")
    print(f"non-dwipada poems with bhavam now:          {have_bh}")


if __name__ == "__main__":
    main()
