"""
Undo the chandassu gold auto-tagging.

Resets rating to NULL for exactly the poems the auto-scan tagged (ids saved in
scripts/gold_autotagged_ids.json), and only if they're still 'gold'. Your 85
hand-picked gold poems are NOT in that list, so they're untouched.

Run:  ./venv/bin/python scripts/gold_scan_undo.py
"""
import sqlite3, json, os

IDS_FILE = os.path.join(os.path.dirname(__file__), "gold_autotagged_ids.json")


def main():
    ids = json.load(open(IDS_FILE))
    con = sqlite3.connect("padyarchana.db")
    con.execute("CREATE TEMP TABLE _u(id INTEGER PRIMARY KEY)")
    con.executemany("INSERT OR IGNORE INTO _u VALUES (?)", [(i,) for i in ids])
    n = con.execute(
        "UPDATE poems SET rating=NULL WHERE rating='gold' AND id IN (SELECT id FROM _u)"
    ).rowcount
    con.commit()
    con.close()
    print(f"reverted {n} auto-tagged poems back to unrated")


if __name__ == "__main__":
    main()
