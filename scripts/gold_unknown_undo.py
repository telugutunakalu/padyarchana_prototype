"""
Undo the unknown-poem auto-classification + gold.

Restores meter_id to the original (unknown) value and resets rating to NULL for
the poems recorded in gold_unknown_undo.json (only those still tagged gold).

Run:  ./venv/bin/python scripts/gold_unknown_undo.py
"""
import sqlite3, json, os

UNDO = os.path.join(os.path.dirname(__file__), "gold_unknown_undo.json")


def main():
    undo = json.load(open(UNDO))
    con = sqlite3.connect("padyarchana.db")
    con.execute("CREATE TEMP TABLE _u(id INTEGER PRIMARY KEY, old_mid INTEGER)")
    con.executemany("INSERT OR IGNORE INTO _u VALUES (?, ?)",
                    [(u["id"], u["old_meter_id"]) for u in undo])
    con.execute(
        "UPDATE poems SET meter_id = (SELECT old_mid FROM _u WHERE _u.id = poems.id) "
        "WHERE id IN (SELECT id FROM _u)"
    )
    n = con.execute(
        "UPDATE poems SET rating=NULL WHERE rating='gold' AND id IN (SELECT id FROM _u)"
    ).rowcount
    con.commit()
    con.close()
    print(f"reverted {len(undo)} poems: meter_id restored, {n} un-golded")


if __name__ == "__main__":
    main()
