"""
Analyze non_dwipada_padartham_results.test5.jsonl and validate that every
result maps cleanly back to a poem in padyarchana.db.

READ-ONLY: makes no changes. Run before onboarding.

Mapping strategy: the key's 6-digit prefix is the global index produced by
scripts/generate_padartham_requests.py. We rebuild the identical ordered list
of poem ids and use ordered_ids[idx] -> poem.id, then cross-check each result's
embedded `poem` text against the DB text.
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
    """Reproduce the exact ordering the generator used."""
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

    n = 0
    idx_out_of_range = 0
    dup_idx = 0
    seen_idx = set()
    text_match = 0
    text_mismatch = []
    empty_pp = 0
    empty_bhavam = 0
    no_result = 0
    pp_entry_total = 0
    bad_pp_keys = 0
    poem_ids = set()

    with open(results_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            n += 1
            d = json.loads(line)
            key = d["key"]
            idx = int(key[:6])
            if idx in seen_idx:
                dup_idx += 1
            seen_idx.add(idx)
            if idx >= len(ordered):
                idx_out_of_range += 1
                continue
            pid = ordered[idx]
            poem_ids.add(pid)

            # text validation
            if norm(d.get("poem")) == norm(text_by_id.get(pid)):
                text_match += 1
            else:
                if len(text_mismatch) < 5:
                    text_mismatch.append((key, pid))

            res = d.get("result") or {}
            if not res or ("prathipadartham" not in res and "bhavam" not in res):
                no_result += 1
                continue
            pp = res.get("prathipadartham") or []
            if not pp:
                empty_pp += 1
            pp_entry_total += len(pp)
            for e in pp:
                if "padam" not in e or "artham" not in e:
                    bad_pp_keys += 1
            if not (res.get("bhavam") or "").strip():
                empty_bhavam += 1

    print(f"results file:           {results_path.name}")
    print(f"records:                {n}")
    print(f"generator ordered ids:  {len(ordered)}")
    print(f"distinct idx:           {len(seen_idx)}  (duplicate idx: {dup_idx})")
    print(f"idx out of range:       {idx_out_of_range}")
    print(f"distinct poem ids hit:  {len(poem_ids)}")
    print(f"poem-text match:        {text_match}/{n}")
    if text_mismatch:
        print(f"  sample mismatches (key, poem_id): {text_mismatch}")
    print(f"records with no result: {no_result}")
    print(f"empty prathipadartham:  {empty_pp}")
    print(f"empty bhavam:           {empty_bhavam}")
    print(f"prathipadartham entries: {pp_entry_total} total"
          f" (avg {pp_entry_total / max(1, n - no_result):.1f}/poem)")
    print(f"entries missing padam/artham keys: {bad_pp_keys}")

    conn.close()


if __name__ == "__main__":
    main()
