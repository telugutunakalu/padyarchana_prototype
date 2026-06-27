"""
Auto-classify + gold the 'unknown'-meter poems that scan 100% as a single meter.

Reads [poem_id, detected_meter] pairs from the browser scan, maps the detected
meter name to a DB meter row (canonical = the row with most poems for that
normalized key; parenthetical yati-variants like "చంపకమాల (సరసీ)" are stripped),
then sets poems.meter_id to the detected meter and rating='gold' (only where the
poem is currently unrated). Writes an undo file (original meter_id per poem).

Usage:
  ./venv/bin/python scripts/gold_unknown_apply.py <pairs_dir> [--dry]
"""
import sqlite3, json, glob, os, sys, re

UNKNOWN = ("unknown", "Unknown", "UNKNOWN")
UNDO = os.path.join(os.path.dirname(__file__), "gold_unknown_undo.json")


def meterKey(n):
    return re.sub(r"(ము|ం)$", "", re.sub(r"\s+", "", n or ""))


def norm_detected(n):
    # strip "(variant, …)" annotation, then normalize the ము/ం ending + spaces
    return meterKey(re.sub(r"\s*\(.*?\)\s*", "", n or ""))


def main(pairs_dir, dry=False):
    pairs = []
    for f in sorted(glob.glob(os.path.join(pairs_dir, "pairs_*.json"))):
        pairs.extend(json.load(open(f)))

    con = sqlite3.connect("padyarchana.db")
    rows = con.execute(
        """SELECT m.id, m.name, COUNT(p.id) c FROM meters m
           LEFT JOIN poems p ON p.meter_id = m.id GROUP BY m.id"""
    ).fetchall()
    bykey = {}
    for mid, name, cnt in rows:
        if name in UNKNOWN:
            continue
        k = meterKey(name)
        if k and (k not in bykey or cnt > bykey[k][2]):
            bykey[k] = (mid, name, cnt)

    updates, unmapped, seen = [], 0, set()
    for pid, det in pairs:
        if pid in seen:
            continue
        seen.add(pid)
        t = bykey.get(norm_detected(det))
        if not t:
            unmapped += 1
            continue
        updates.append((pid, t[0]))

    print(f"perfect-match pairs: {len(pairs)} | mapped: {len(updates)} | unmapped(skipped): {unmapped}")

    con.execute("CREATE TEMP TABLE _map(id INTEGER PRIMARY KEY, mid INTEGER)")
    con.executemany("INSERT OR IGNORE INTO _map(id, mid) VALUES (?, ?)", updates)

    # undo snapshot: current meter_id for each poem we're about to reclassify
    old = dict(con.execute(
        "SELECT id, meter_id FROM poems WHERE id IN (SELECT id FROM _map)"
    ).fetchall())
    json.dump([{"id": pid, "old_meter_id": old.get(pid)} for pid, _ in updates],
              open(UNDO, "w"))
    print(f"undo list saved -> {UNDO}")

    if dry:
        print("DRY RUN — no changes written.")
        con.close()
        return

    con.execute(
        "UPDATE poems SET meter_id = (SELECT mid FROM _map WHERE _map.id = poems.id) "
        "WHERE id IN (SELECT id FROM _map)"
    )
    golded = con.execute(
        "UPDATE poems SET rating='gold' WHERE rating IS NULL AND id IN (SELECT id FROM _map)"
    ).rowcount
    con.commit()
    print(f"applied: reclassified {len(updates)} poems, golded {golded}")
    con.close()


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args[0], dry="--dry" in sys.argv)
